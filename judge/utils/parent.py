"""Helpers for the Parent Portal: stats aggregation, prompt building, and
the orchestration function that calls OpenAI and persists the result.

All "live page" helpers are wrapped with @cache_wrapper so the parent
dashboard renders fast even with cold OpenAI cron data. The AI text itself
is NOT cached here — it lives in the ChildAIAssessment row in the DB.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from django.db.models import Count, Q, Avg

from judge.caching import cache_wrapper
from judge.models import (
    ChildAIAssessment,
    Organization,
    Problem,
    ProblemType,
    Profile,
    Submission,
)
from judge.utils.problems import user_completed_ids
from judge.models.submission import get_user_submission_dates


# --------------------------------------------------------------------------
# Date utilities
# --------------------------------------------------------------------------
def monday_of_week_for(d: date) -> date:
    """Return the Monday that *starts* the week containing `d`.

    Sunday is treated as the LAST day of its week (Mon-Sun), so Sunday's
    Monday is 6 days earlier. This makes the cron job (which fires on
    Sunday) attribute the run to the week that just ended.
    """
    # weekday(): Mon=0 ... Sun=6
    return d - timedelta(days=d.weekday())


def current_week_start() -> date:
    return monday_of_week_for(date.today())


# --------------------------------------------------------------------------
# Per-child summary stats (cached, used on dashboard cards + overview)
# --------------------------------------------------------------------------
def get_display_name(user) -> str:
    """Họ và tên (first + last) if set, else fall back to username."""
    full = f"{user.first_name} {user.last_name}".strip()
    return full or user.username


@cache_wrapper(prefix="psum_v2", timeout=600)
def get_child_summary(child_id: int) -> dict:
    profile = Profile.objects.select_related("user").get(id=child_id)
    thirty_days_ago = date.today() - timedelta(days=30)
    subs_30d = Submission.objects.filter(user_id=child_id, date__gte=thirty_days_ago)
    total_30d = subs_30d.count()
    ac_30d = subs_30d.filter(result="AC").count()

    last_sub = (
        Submission.objects.filter(user_id=child_id)
        .order_by("-date")
        .values_list("date", flat=True)
        .first()
    )

    return {
        "id": profile.id,
        "username": profile.user.username,
        "display_name": get_display_name(profile.user),
        "image_url": profile.get_profile_image_url(),
        "problems_solved": profile.get_problem_count(),
        "points": profile.get_points(),
        "performance_points": profile.get_performance_points(),
        "rating": profile.get_rating(),
        "submission_count_30d": total_30d,
        "correct_count_30d": ac_30d,
        "correct_rate_30d": round(ac_30d * 100.0 / total_30d, 1) if total_30d else 0.0,
        "last_submitted": last_sub,
    }


@cache_wrapper(prefix="ptop", timeout=600)
def get_topic_breakdown(child_id: int) -> list[dict]:
    """Per problem-type AC/attempt counts for the child."""
    rows = (
        Submission.objects
        .filter(user_id=child_id)
        .values("problem__types__id", "problem__types__full_name")
        .annotate(
            attempted=Count("id"),
            ac=Count("id", filter=Q(result="AC")),
        )
        .order_by("-attempted")
    )
    out = []
    for r in rows:
        if r["problem__types__id"] is None:
            continue
        attempted = r["attempted"] or 0
        ac = r["ac"] or 0
        out.append({
            "type_id": r["problem__types__id"],
            "type_name": r["problem__types__full_name"],
            "attempted": attempted,
            "ac": ac,
            "ac_rate": round(ac * 100.0 / attempted, 1) if attempted else 0.0,
        })
    return out


@cache_wrapper(prefix="pcavg", timeout=600)
def get_class_averages(organization_id: int) -> dict:
    """Average problem_count / points across all members of the organization."""
    agg = Profile.objects.filter(organizations__id=organization_id).aggregate(
        avg_problems=Avg("problem_count"),
        avg_points=Avg("points"),
        avg_perf=Avg("performance_points"),
    )
    return {
        "organization_id": organization_id,
        "avg_problems_solved": round(agg["avg_problems"] or 0, 1),
        "avg_points": round(agg["avg_points"] or 0, 1),
        "avg_performance_points": round(agg["avg_perf"] or 0, 1),
    }


def get_child_class_compare(child_id: int) -> dict | None:
    """If child belongs to an Organization, return their first one with avgs."""
    profile = Profile.objects.prefetch_related("organizations").get(id=child_id)
    org = profile.organizations.first()
    if not org:
        return None
    summary = get_child_summary(child_id)
    avgs = get_class_averages(org.id)
    return {
        "organization_name": org.name,
        "child_problems_solved": summary["problems_solved"],
        "avg_problems_solved": avgs["avg_problems_solved"],
        "child_points": summary["points"],
        "avg_points": avgs["avg_points"],
        "child_performance_points": summary["performance_points"],
        "avg_performance_points": avgs["avg_performance_points"],
    }


# --------------------------------------------------------------------------
# Contest helpers
# --------------------------------------------------------------------------
def get_upcoming_contests(limit: int = 3):
    """Visible, public contests that haven't started yet (Vietnam time)."""
    from django.utils import timezone
    from judge.models import Contest

    now = timezone.now()
    return list(
        Contest.objects
        .filter(is_visible=True, start_time__gt=now)
        .order_by("start_time")[:limit]
    )


def get_child_contest_history(child_id: int, limit: int = 5):
    """Recent ContestParticipation for the child (visible contests only)."""
    from judge.models import ContestParticipation

    return list(
        ContestParticipation.objects
        .filter(user_id=child_id, virtual=0, contest__is_visible=True)
        .select_related("contest", "rating")
        .order_by("-real_start")[:limit]
    )


# --------------------------------------------------------------------------
# Heatmap reuse
# --------------------------------------------------------------------------
def get_heatmap(child_id: int) -> dict:
    """Wrapper around the existing cached helper so view doesn't need to import it."""
    return get_user_submission_dates(child_id)


# --------------------------------------------------------------------------
# Weakness detection + suggestion
# --------------------------------------------------------------------------
def get_weakness_types(
    child_id: int,
    threshold: float = 40.0,
    min_attempts: int = 3,
) -> list[dict]:
    """Return topic rows where AC rate < threshold and attempts >= min_attempts."""
    return [
        t
        for t in get_topic_breakdown(child_id)
        if t["attempted"] >= min_attempts and t["ac_rate"] < threshold
    ]


def get_suggested_problems(
    child_id: int,
    weakness_type_ids: Iterable[int],
    limit: int = 5,
) -> list[Problem]:
    """Public unsolved problems matching weakness topics; falls back to easy unsolved."""
    profile = Profile.objects.get(id=child_id)
    solved = user_completed_ids(profile)

    qs = Problem.objects.filter(is_public=True).exclude(id__in=solved)
    if weakness_type_ids:
        qs = qs.filter(types__id__in=list(weakness_type_ids)).distinct()
    return list(qs.order_by("points")[:limit])


# --------------------------------------------------------------------------
# AI prompt + orchestration
# --------------------------------------------------------------------------
PROMPT_TEMPLATE = """\
Bạn là gia sư Tin học có nhiều năm kinh nghiệm dạy học sinh THCS/THPT.
Hãy phân tích tình hình học tập của học sinh dưới đây và viết một báo cáo
ngắn gọn dành cho phụ huynh — không dùng thuật ngữ kỹ thuật khó hiểu.

THÔNG TIN HỌC SINH
- Tên: {name}
- Lớp/Tổ chức: {organization_name}
- Tổng số bài đã giải: {problems_solved}
- Điểm tích lũy: {points}
- Performance points: {performance_points}
- Rating contest: {rating}
- Số bài nộp 30 ngày qua: {sub_30d}
- Tỉ lệ AC 30 ngày qua: {ac_rate_30d}%

HIỆU SUẤT THEO CHỦ ĐỀ (chủ đề · đã làm · AC · tỉ lệ AC)
{topic_table}

CONTEST GẦN ĐÂY
{contest_table}

DANH SÁCH BÀI ĐƯỢC ĐỀ XUẤT (đã chọn sẵn, không bịa thêm bài khác)
{suggested_table}

YÊU CẦU OUTPUT (Markdown, tiếng Việt)
## Tổng quan tình hình
3-4 câu súc tích về xu hướng học tập của con.

## Điểm mạnh
- 3 gạch đầu dòng, dựa trên topic AC rate cao và performance points.

## Cần cải thiện
- 3 gạch đầu dòng, mỗi dòng nêu chủ đề yếu cụ thể + giải thích ngắn vì sao.

## Gợi ý luyện tập tuần tới
Liệt kê đúng các bài trong "DANH SÁCH BÀI ĐƯỢC ĐỀ XUẤT" ở trên (giữ nguyên
mã bài). Với mỗi bài, viết 1 câu giải thích vì sao bài này khớp với điểm
yếu hiện tại của con.
"""


def _format_topic_table(rows: list[dict]) -> str:
    if not rows:
        return "  (chưa đủ dữ liệu)"
    return "\n".join(
        f"- {r['type_name']}: {r['attempted']} bài / AC {r['ac']} ({r['ac_rate']}%)"
        for r in rows[:10]
    )


def _format_contest_table(child_id: int) -> str:
    from judge.utils.users import get_contest_ratings  # local import — avoid early model evaluation

    rows = get_contest_ratings(child_id)[:5]
    if not rows:
        return "  (chưa tham gia contest có rating)"
    return "\n".join(
        f"- {r.get('contest_name', 'Contest')}: rating {r.get('rating', '?')}, "
        f"hạng {r.get('rank', '?')}"
        for r in rows
    )


def _format_suggested_table(problems: list[Problem]) -> str:
    if not problems:
        return "  (không có)"
    return "\n".join(
        f"- [{p.code}] {p.name} (chủ đề: {p.get_types_name()})" for p in problems
    )


def build_assessment_prompt(child_id: int) -> tuple[str, list[str]]:
    """Build the prompt + return the suggested-problem codes alongside it."""
    profile = Profile.objects.prefetch_related("organizations").get(id=child_id)
    summary = get_child_summary(child_id)
    topic_rows = get_topic_breakdown(child_id)
    weakness = get_weakness_types(child_id)
    weakness_ids = [t["type_id"] for t in weakness]
    suggested = get_suggested_problems(child_id, weakness_ids, limit=5)

    org = profile.organizations.first()
    prompt = PROMPT_TEMPLATE.format(
        name=profile.user.username,
        organization_name=org.name if org else "(chưa thuộc lớp nào)",
        problems_solved=summary["problems_solved"],
        points=summary["points"],
        performance_points=summary["performance_points"],
        rating=summary["rating"] if summary["rating"] is not None else "(chưa có)",
        sub_30d=summary["submission_count_30d"],
        ac_rate_30d=summary["ac_rate_30d"],
        topic_table=_format_topic_table(topic_rows),
        contest_table=_format_contest_table(child_id),
        suggested_table=_format_suggested_table(suggested),
    )
    return prompt, [p.code for p in suggested]


def generate_assessment(
    child_id: int,
    model: str | None = None,
    force_week_start: date | None = None,
) -> ChildAIAssessment:
    """Build prompt → call OpenAI → upsert ChildAIAssessment row.

    Idempotent for a given (child, week_start). Caller can pass
    `force_week_start` to regenerate a specific week (e.g. admin action).
    """
    from judge.utils.openai_client import call_openai

    week_start = force_week_start or current_week_start()
    prompt, codes = build_assessment_prompt(child_id)
    result = call_openai(prompt, model=model, max_tokens=2000)

    obj, _ = ChildAIAssessment.objects.update_or_create(
        child_id=child_id,
        week_start=week_start,
        defaults=dict(
            markdown=result["text"],
            suggested_problem_codes=codes,
            model_used=result["model"],
            prompt_tokens=result["prompt_tokens"],
            completion_tokens=result["completion_tokens"],
        ),
    )
    return obj
