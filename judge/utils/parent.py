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


@cache_wrapper(prefix="psum_v10", timeout=60)
def get_child_summary(child_id: int) -> dict:
    """Compute parent dashboard stats for a child.

    `problems_solved` and `points` INCLUDE contest contributions (both live
    and virtual). Definition:
      - problems_solved = distinct problems with AC OR contest submission
                          that earned positive points (partial credit counts).
      - points          = Profile.points (public AC accumulation) PLUS sum of
                          ContestParticipation.score across all participations.
    `correct_rate_30d` is the AVERAGE of per-problem AC ratios in the last 30
    days. Also includes today-only counters for the dashboard alert.
    """
    from django.db.models import Count, Q, Sum
    from judge.models import ContestParticipation

    profile = Profile.objects.select_related("user").get(id=child_id)
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    all_subs = Submission.objects.filter(user_id=child_id)
    total_submissions = all_subs.count()

    # "Giải đúng" = strictly AC (full marks) on PUBLIC problems, so it is always
    # ≤ problem_count (which also counts partial-credit). Keeps the card's two
    # "bài" numbers consistent (đã giải đúng ≤ tổng số bài đã giải).
    problems_solved_total = (
        all_subs
        .filter(result="AC", problem__is_public=True)
        .values_list("problem_id", flat=True)
        .distinct()
        .count()
    )

    # "Điểm tích lũy" — for each problem the child has touched, take only the
    # HIGHEST-scoring submission and sum across problems. Includes both regular
    # and contest submissions (Submission.points is on the problem's natural
    # scale regardless of context).
    from django.db.models import Max
    best_per_problem = (
        all_subs
        .values("problem_id")
        .annotate(best=Max("points"))
        .values_list("best", flat=True)
    )
    points_total = round(sum(float(x or 0) for x in best_per_problem), 1)

    subs_30d = all_subs.filter(date__gte=thirty_days_ago)
    total_30d = subs_30d.count()
    ac_30d = subs_30d.filter(result="AC").count()

    # Today's activity (timezone-naive, server local).
    # "Solved" counts both:
    #   - AC submissions (full marks), and
    #   - Contest submissions with positive points (partial credit during a contest)
    # so that partial contest solves are recognised the way they normally are
    # in olympiad scoring.
    subs_today = all_subs.filter(date__date=today)
    submissions_today = subs_today.count()
    ac_today = subs_today.filter(result="AC").count()
    # "Solved today" = problems whose FIRST solve falls on today (so the daily
    # totals across days sum to the all-time distinct count, not double-counted).
    solve_q = Q(result="AC") | Q(contest_object__isnull=False, points__gt=0)
    todays_candidates = set(
        subs_today.filter(solve_q).values_list("problem_id", flat=True).distinct()
    )
    if todays_candidates:
        from django.db.models import Min
        first_solve = (
            Submission.objects
            .filter(user_id=child_id, problem_id__in=todays_candidates)
            .filter(solve_q)
            .values("problem_id")
            .annotate(first_date=Min("date"))
        )
        solved_problems_today = sum(
            1 for r in first_solve if r["first_date"].date() == today
        )
    else:
        solved_problems_today = 0

    # Current calendar week (Mon→Sun): distinct problems NEWLY solved this week
    # (first solve on/after Monday). Drives the weekly progress widget +
    # "dưới 10 bài/tuần" red warning. Resets every Monday.
    week_start_date = monday_of_week_for(today)
    subs_7d = all_subs.filter(date__date__gte=week_start_date)
    submissions_7d = subs_7d.count()
    week_candidates = set(
        subs_7d.filter(solve_q).values_list("problem_id", flat=True).distinct()
    )
    if week_candidates:
        from django.db.models import Min
        first_solve_week = (
            Submission.objects
            .filter(user_id=child_id, problem_id__in=week_candidates)
            .filter(solve_q)
            .values("problem_id")
            .annotate(first_date=Min("date"))
        )
        solved_problems_7d = sum(
            1 for r in first_solve_week if r["first_date"].date() >= week_start_date
        )
    else:
        solved_problems_7d = 0

    # Per-problem AC ratio averaged across problems touched in the last 30d.
    per_problem = (
        subs_30d
        .values("problem_id")
        .annotate(
            total=Count("id"),
            ac=Count("id", filter=Q(result="AC")),
        )
    )
    ratios = [(row["ac"] * 100.0 / row["total"]) for row in per_problem if row["total"]]
    correct_rate_30d = round(sum(ratios) / len(ratios), 1) if ratios else 0.0

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
        "problems_solved": problems_solved_total,
        "problem_count": profile.problem_count,
        "points": points_total,
        "performance_points": profile.get_performance_points(),
        "rating": profile.get_rating(),
        "total_submissions": total_submissions,
        "submission_count_30d": total_30d,
        "correct_count_30d": ac_30d,
        "problems_attempted_30d": len(ratios),
        "correct_rate_30d": correct_rate_30d,
        "submissions_today": submissions_today,
        "ac_today": ac_today,
        "solved_problems_today": solved_problems_today,
        "solved_problems_7d": solved_problems_7d,
        "submissions_7d": submissions_7d,
        "last_submitted": last_sub,
    }


@cache_wrapper(prefix="ptop_v2", timeout=600)
def get_topic_breakdown(child_id: int) -> list[dict]:
    """Per problem-type stats counted by DISTINCT problems (not submissions).

    For each topic:
      - attempted: số bài đã làm trong chủ đề
      - ac:        số bài có ít nhất 1 lần giải đúng
      - ac_rate:   TRUNG BÌNH tỉ lệ đúng/bài (giống công thức 30-ngày trên).
                   VD: bài 1 đúng 1/1 (100%), bài 2 đúng 1/3 (33%) → 66.5%
    """
    rows = (
        Submission.objects
        .filter(user_id=child_id)
        .values(
            "problem__types__id",
            "problem__types__full_name",
            "problem_id",
        )
        .annotate(
            sub_total=Count("id"),
            sub_ac=Count("id", filter=Q(result="AC")),
        )
    )

    # Group by type → list of per-problem ratios.
    by_type: dict[int, dict] = {}
    for r in rows:
        tid = r["problem__types__id"]
        if tid is None:
            continue
        entry = by_type.setdefault(
            tid,
            {"name": r["problem__types__full_name"], "ratios": [], "ac_count": 0},
        )
        ratio = r["sub_ac"] * 100.0 / r["sub_total"] if r["sub_total"] else 0.0
        entry["ratios"].append(ratio)
        if r["sub_ac"] > 0:
            entry["ac_count"] += 1

    out = []
    for tid, d in by_type.items():
        attempted = len(d["ratios"])
        out.append({
            "type_id": tid,
            "type_name": d["name"],
            "attempted": attempted,        # distinct problems attempted in this topic
            "ac": d["ac_count"],            # distinct problems with ≥1 AC
            "ac_rate": round(sum(d["ratios"]) / attempted, 1) if attempted else 0.0,
        })
    out.sort(key=lambda r: -r["attempted"])
    return out


@cache_wrapper(prefix="pcavg_v5", timeout=60)
def get_class_averages(teacher_class_id: int) -> dict:
    """Average stats across students of the TeacherClass.

    Uses the SAME definitions as `get_child_summary` so the "con bạn vs TB lớp"
    comparison is apples-to-apples.
    """
    from django.db.models import Sum, Max
    from judge.models import TeacherClass, Student

    try:
        cls = TeacherClass.objects.get(id=teacher_class_id)
    except TeacherClass.DoesNotExist:
        return {
            "teacher_class_id": teacher_class_id,
            "avg_problems_solved": 0.0,
            "avg_points": 0.0,
            "avg_performance_points": 0.0,
        }
    # Only students with an OJ Profile contribute to OJ-stat averages.
    member_ids = list(
        Student.objects.filter(teacher_class=cls, profile__isnull=False)
        .values_list("profile_id", flat=True)
    )
    n = len(member_ids)
    if n == 0:
        return {
            "teacher_class_id": teacher_class_id,
            "avg_problems_solved": 0.0,
            "avg_points": 0.0,
            "avg_performance_points": 0.0,
        }

    profile_agg = Profile.objects.filter(id__in=member_ids).aggregate(
        sum_perf=Sum("performance_points"),
    )
    sum_perf = float(profile_agg["sum_perf"] or 0)

    best_rows = (
        Submission.objects
        .filter(user_id__in=member_ids)
        .values("user_id", "problem_id")
        .annotate(best=Max("points"))
        .values_list("best", flat=True)
    )
    sum_best_points = float(sum((x or 0) for x in best_rows))

    distinct_user_problem = (
        Submission.objects
        .filter(user_id__in=member_ids, result="AC")
        .values("user_id", "problem_id")
        .distinct()
        .count()
    )

    return {
        "teacher_class_id": teacher_class_id,
        "avg_problems_solved": round(distinct_user_problem / n, 1),
        "avg_points": round(sum_best_points / n, 1),
        "avg_performance_points": round(sum_perf / n, 1),
    }


def get_child_class_compare(child_id: int) -> dict | None:
    """If child has a Student row tied to a TeacherClass, return averages."""
    from judge.models import Student
    student = Student.objects.filter(profile_id=child_id).select_related("teacher_class").first()
    if not student:
        return None
    cls = student.teacher_class
    summary = get_child_summary(child_id)
    avgs = get_class_averages(cls.id)
    return {
        "organization_name": cls.name,
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
def get_child_day_activity(child_id: int, on_date: date) -> dict:
    """Submission/AC counts for a child on a specific calendar day.

    Used by the parent dashboard date navigator.
    """
    from django.db.models import Q, Sum
    from judge.models import ContestSubmission

    subs = Submission.objects.filter(user_id=child_id, date__date=on_date)
    submissions = subs.count()
    ac_subs = subs.filter(result="AC").count()
    # Count problems whose FIRST-time solve happened on this day (no double-counting
    # if the same problem is also "solved" on other days). A "solve" = AC or
    # positive-point contest submission.
    solve_q = Q(result="AC") | Q(contest_object__isnull=False, points__gt=0)
    problems_today = set(
        subs.filter(solve_q).values_list("problem_id", flat=True).distinct()
    )
    if problems_today:
        # For each candidate problem, was there an earlier solve before this day?
        from django.db.models import Min
        first_solve = (
            Submission.objects
            .filter(user_id=child_id, problem_id__in=problems_today)
            .filter(solve_q)
            .values("problem_id")
            .annotate(first_date=Min("date"))
        )
        solved_problems = sum(
            1 for r in first_solve if r["first_date"].date() == on_date
        )
    else:
        solved_problems = 0
    # Best score per problem TODAY (so re-submitting the same problem doesn't
    # inflate the daily total). Uses Submission.points (problem-natural scale).
    from django.db.models import Max
    best_per_problem = (
        subs.values("problem_id").annotate(best=Max("points")).values_list("best", flat=True)
    )
    pts_today = sum(float(x or 0) for x in best_per_problem)
    return {
        "date": on_date,
        "submissions": submissions,
        "ac_submissions": ac_subs,
        "solved_problems": solved_problems,
        "points": round(pts_today, 1),
        "is_today": on_date == date.today(),
    }


def get_child_week_activity(child_id: int, in_week_of: date) -> dict:
    """Newly-solved problems in the Mon→Sun week CONTAINING `in_week_of`.

    Follows the date navigator: when the parent steps back to an earlier date,
    the weekly box reflects that date's calendar week (not the current week).
    """
    from django.db.models import Q, Min

    week_start = monday_of_week_for(in_week_of)
    week_end = week_start + timedelta(days=6)
    subs = Submission.objects.filter(
        user_id=child_id, date__date__gte=week_start, date__date__lte=week_end
    )
    submissions = subs.count()
    solve_q = Q(result="AC") | Q(contest_object__isnull=False, points__gt=0)
    candidates = set(
        subs.filter(solve_q).values_list("problem_id", flat=True).distinct()
    )
    if candidates:
        first_solve = (
            Submission.objects
            .filter(user_id=child_id, problem_id__in=candidates)
            .filter(solve_q)
            .values("problem_id")
            .annotate(first_date=Min("date"))
        )
        solved = sum(
            1 for r in first_solve if week_start <= r["first_date"].date() <= week_end
        )
    else:
        solved = 0
    return {
        "week_start": week_start,
        "week_end": week_end,
        "solved_problems": solved,
        "submissions": submissions,
        "is_current_week": week_start == monday_of_week_for(date.today()),
    }


def get_child_month_calendar(child_id: int, year: int, month: int) -> dict:
    """Per-day newly-solved counts for a calendar month → heatmap data.

    Returns weeks (list of list of cells) covering the month grid (Mon-first),
    each cell: {date, in_month, is_future, solved, submissions, tier}.
    `tier` drives the colour: 0=empty, low/mid/high by count.
    """
    from calendar import Calendar
    from django.db.models import Q, Min, Count
    from django.db.models.functions import TruncDate

    today = date.today()
    solve_q = Q(result="AC") | Q(contest_object__isnull=False, points__gt=0)

    # Distinct problems' FIRST solve date (global), bucketed into this month.
    solved_by_day: dict[int, int] = {}
    first_solves = (
        Submission.objects.filter(user_id=child_id).filter(solve_q)
        .values("problem_id").annotate(fd=Min("date"))
    )
    for r in first_solves:
        d = r["fd"].date()
        if d.year == year and d.month == month:
            solved_by_day[d.day] = solved_by_day.get(d.day, 0) + 1

    # Submissions per day in the month.
    subs_by_day = {
        row["d"].day: row["c"]
        for row in (
            Submission.objects
            .filter(user_id=child_id, date__year=year, date__month=month)
            .annotate(d=TruncDate("date")).values("d").annotate(c=Count("id"))
        )
    }

    def tier(n: int) -> int:
        if n == 0:
            return 0
        if n <= 2:
            return 1
        if n <= 5:
            return 2
        return 3

    weeks = []
    month_solved = 0
    active_days = 0
    for week in Calendar(firstweekday=0).monthdatescalendar(year, month):
        row = []
        for d in week:
            in_month = (d.month == month and d.year == year)
            n = solved_by_day.get(d.day, 0) if in_month else 0
            if in_month:
                month_solved += n
                if n > 0:
                    active_days += 1
            row.append({
                "date": d,
                "day": d.day,
                "in_month": in_month,
                "is_future": d > today,
                "is_today": d == today,
                "solved": n,
                "submissions": subs_by_day.get(d.day, 0) if in_month else 0,
                "tier": tier(n) if (in_month and d <= today) else -1,
            })
        weeks.append(row)
    return {
        "year": year, "month": month, "weeks": weeks,
        "month_solved": month_solved, "active_days": active_days,
    }


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


# --------------------------------------------------------------------------
# Class schedule helpers
# --------------------------------------------------------------------------
DAY_NAMES_VN = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def get_child_schedule(child_id: int) -> list[dict]:
    """Return weekly schedule grouped by day for the child's TeacherClass(es).

    Looks up TeacherClass via Student rows that reference this child's Profile.
    Output: [{day_index, day_name, lessons: [ClassSchedule, ...]}] for all 7 days
    (empty list when no lesson). Returns [] when child has no class.
    """
    from judge.models import ClassSchedule, Student

    cls_ids = list(
        Student.objects.filter(profile_id=child_id).values_list("teacher_class_id", flat=True)
    )
    if not cls_ids:
        return []

    rows = list(
        ClassSchedule.objects
        .filter(teacher_class_id__in=cls_ids, is_active=True)
        .select_related("teacher_class")
        .order_by("day_of_week", "start_time")
    )
    if not rows:
        return []

    by_day = {i: [] for i in range(7)}
    for r in rows:
        by_day[r.day_of_week].append(r)
    return [
        {"day_index": i, "day_name": DAY_NAMES_VN[i], "lessons": by_day[i]}
        for i in range(7)
    ]


def get_next_lesson(child_id: int):
    """Find the upcoming lesson within the next 7 days (or None)."""
    from datetime import datetime
    from judge.models import ClassSchedule, Student

    cls_ids = list(
        Student.objects.filter(profile_id=child_id).values_list("teacher_class_id", flat=True)
    )
    if not cls_ids:
        return None

    rows = list(
        ClassSchedule.objects
        .filter(teacher_class_id__in=cls_ids, is_active=True)
        .order_by("day_of_week", "start_time")
    )
    if not rows:
        return None

    now = datetime.now()
    today_dow = now.weekday()                  # Mon=0..Sun=6
    now_t = now.time()

    # Next lesson today (later than now), then forward through the week.
    for offset in range(7):
        dow = (today_dow + offset) % 7
        for r in rows:
            if r.day_of_week != dow:
                continue
            if offset == 0 and r.start_time <= now_t:
                continue
            days_ahead = offset
            return {
                "lesson": r,
                "day_name": DAY_NAMES_VN[dow],
                "is_today": offset == 0,
                "is_tomorrow": offset == 1,
                "days_ahead": days_ahead,
            }
    return None


def get_child_contest_history(child_id: int, limit: int = 5):
    """Recent ContestParticipation for the child.

    Includes BOTH live (virtual=0) and virtual (virtual>=1) participations
    so that parents see all the contests the child has attempted —
    even re-runs/practice mode after the contest ended. Spectate-only
    participations (no real start) are still excluded via `real_start__isnull=False`.
    """
    from judge.models import ContestParticipation

    return list(
        ContestParticipation.objects
        .filter(
            user_id=child_id,
            contest__is_visible=True,
            real_start__isnull=False,
        )
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
- Tỉ lệ giải đúng 30 ngày qua: {correct_rate_30d}%

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
    from judge.models import Student
    profile = Profile.objects.get(id=child_id)
    summary = get_child_summary(child_id)
    topic_rows = get_topic_breakdown(child_id)
    weakness = get_weakness_types(child_id)
    weakness_ids = [t["type_id"] for t in weakness]
    suggested = get_suggested_problems(child_id, weakness_ids, limit=5)

    student = Student.objects.filter(profile_id=child_id).select_related("teacher_class").first()
    cls = student.teacher_class if student else None
    prompt = PROMPT_TEMPLATE.format(
        name=profile.user.username,
        organization_name=cls.name if cls else "(chưa thuộc lớp nào)",
        problems_solved=summary["problems_solved"],
        points=summary["points"],
        performance_points=summary["performance_points"],
        rating=summary["rating"] if summary["rating"] is not None else "(chưa có)",
        sub_30d=summary["submission_count_30d"],
        correct_rate_30d=summary["correct_rate_30d"],
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


# ==========================================================================
# Class-level ranking + weekly AI summary (Teacher Portal)
# ==========================================================================
def get_class_ranking(cls_id: int) -> list[dict]:
    """Bảng xếp hạng học sinh trong lớp (chỉ HS có account OJ).

    Trả về list dict đã xếp hạng theo tổng điểm (points), tie-break theo
    performance points. Mỗi dict có thêm `rank_*` cho từng chỉ số để hiển thị.
    """
    from judge.models import Student

    students = (
        Student.objects.filter(teacher_class_id=cls_id, profile__isnull=False)
        .select_related("profile__user")
    )
    rows = []
    for s in students:
        p = s.profile
        summ = get_child_summary(p.id)  # cached; reuse for consistent AC stats
        rows.append({
            "student": s,
            "name": s.display_name,
            "username": p.user.username,
            "points": round(p.points or 0, 1),
            "performance_points": round(p.performance_points or 0, 1),
            "problem_count": p.problem_count or 0,
            "ac_solved": summ["problems_solved"],
            "correct_rate": summ["correct_rate_30d"],
            "rating": p.rating,
        })
    # primary ranking: tổng điểm
    rows.sort(key=lambda r: (-r["points"], -r["performance_points"], -r["problem_count"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def _activity_tier(n: int) -> int:
    if n == 0:
        return 0
    if n <= 2:
        return 1
    if n <= 5:
        return 2
    return 3


def get_class_daily_matrix(cls_id: int, start_date: date, end_date: date) -> dict:
    """Per-student × per-day newly-solved-problem counts over [start, end].

    "Solved" matches the ranking's "Bài đã giải" metric EXACTLY
    (Profile.problem_count): distinct PUBLIC problems on which the student
    earned positive points (full AC OR partial credit), counted on the date of
    the problem's FIRST positive-scoring submission. So row totals reconcile
    with the ranking column.
    """
    from judge.models import Student
    from django.db.models import Min

    days = []
    d = start_date
    while d <= end_date:
        days.append(d)
        d += timedelta(days=1)

    students = (
        Student.objects.filter(teacher_class_id=cls_id, profile__isnull=False)
        .select_related("profile__user")
    )
    rows = []
    for s in students:
        cid = s.profile_id
        per_day: dict[date, int] = {}
        first_solves = (
            Submission.objects
            .filter(user_id=cid, points__gt=0, problem__is_public=True)
            .values("problem_id").annotate(fd=Min("date"))
        )
        for r in first_solves:
            dd = r["fd"].date()
            if start_date <= dd <= end_date:
                per_day[dd] = per_day.get(dd, 0) + 1
        cells = [{"n": per_day.get(dy, 0), "tier": _activity_tier(per_day.get(dy, 0))}
                 for dy in days]
        rows.append({
            "student": s,
            "name": s.display_name,
            "username": s.profile.user.username,
            "cells": cells,
            "total": sum(c["n"] for c in cells),
        })
    rows.sort(key=lambda r: -r["total"])
    return {"days": days, "rows": rows, "num_days": len(days)}


def _format_class_ranking_table(rows: list[dict]) -> str:
    if not rows:
        return "  (lớp chưa có học sinh nào gắn account OJ)"
    lines = ["# | Học sinh | Bài đã giải | Tổng điểm | Performance | Rating"]
    for r in rows:
        rating = r["rating"] if r["rating"] is not None else "—"
        lines.append(
            f"{r['rank']} | {r['name']} | {r['problem_count']} | "
            f"{r['points']} | {r['performance_points']} | {rating}"
        )
    return "\n".join(lines)


CLASS_PROMPT_TEMPLATE = """Bạn là giáo viên chủ nhiệm một lớp luyện thi Tin học (THCS/THPT).
Hãy viết một bản TỔNG KẾT TUẦN ngắn gọn cho lớp dưới đây, gửi cho giáo viên,
bằng tiếng Việt, văn phong thân thiện, KHÔNG dùng thuật ngữ quá kỹ thuật.

THÔNG TIN LỚP:
- Tên lớp: {class_name}
- Sĩ số (có account OJ): {n_students}
- Tổng số bài đã giải của cả lớp: {total_solved}
- Số lần nộp bài 7 ngày qua: {sub_7d}

BẢNG XẾP HẠNG (theo tổng điểm):
{ranking_table}

YÊU CẦU OUTPUT (Markdown, tiếng Việt), gồm các mục:
## Tổng quan tuần
3-4 câu về tình hình chung của lớp.

## Điểm sáng
- 2-3 gạch đầu dòng: bạn nào nổi bật, tiến bộ, dẫn đầu.

## Cần quan tâm
- 2-3 gạch đầu dòng: bạn nào đang đứng sau / ít hoạt động, nên hỗ trợ thêm.

## Gợi ý cho giáo viên
- 2-3 gợi ý hành động cụ thể cho tuần tới (chủ đề nên ôn, cách phân nhóm...).
"""


def build_class_summary_prompt(cls_id: int) -> str:
    from judge.models import TeacherClass, Submission
    from django.utils import timezone

    cls = TeacherClass.objects.get(id=cls_id)
    rows = get_class_ranking(cls_id)
    profile_ids = [r["student"].profile_id for r in rows]
    since = timezone.now() - timedelta(days=7)
    sub_7d = Submission.objects.filter(
        user_id__in=profile_ids, date__gte=since
    ).count() if profile_ids else 0
    return CLASS_PROMPT_TEMPLATE.format(
        class_name=cls.name,
        n_students=len(rows),
        total_solved=sum(r["problem_count"] for r in rows),
        sub_7d=sub_7d,
        ranking_table=_format_class_ranking_table(rows),
    )


def generate_class_summary(
    cls_id: int,
    model: str | None = None,
    force_week_start: date | None = None,
):
    """Build prompt → call OpenAI → upsert ClassAISummary row (1/lớp/tuần)."""
    from judge.models import ClassAISummary
    from judge.utils.openai_client import call_openai

    week_start = force_week_start or current_week_start()
    prompt = build_class_summary_prompt(cls_id)
    result = call_openai(prompt, model=model, max_tokens=1500)

    obj, _ = ClassAISummary.objects.update_or_create(
        teacher_class_id=cls_id,
        week_start=week_start,
        defaults=dict(
            markdown=result["text"],
            model_used=result["model"],
            prompt_tokens=result["prompt_tokens"],
            completion_tokens=result["completion_tokens"],
        ),
    )
    return obj
