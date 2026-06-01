"""Teacher Portal views — class management for Dana Academy.

Teachers (Profile.display_rank == "teacher") and staff users access /teacher/
(non-staff teachers get redirected here by middleware).

A *class* is a TeacherClass; its *roster* is the set of Student rows pointing
at it. Student.profile is OPTIONAL — students without an OJ account are
tracked via Student row only (attendance/tuition/academic still work, but
they have no OJ stats and can't be linked to parent users).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from judge.models import (
    AcademicLevel,
    Attendance,
    ClassAISummary,
    ClassSchedule,
    ParentContact,
    Profile,
    SessionNote,
    Student,
    TeacherClass,
    TuitionRecord,
)
from judge.models.teacher import ACADEMIC_LEVEL_CHOICES


class TeacherRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        prof = getattr(request, "profile", None)
        if not prof or (not prof.is_teacher and not request.user.is_staff):
            return HttpResponseForbidden("Trang này chỉ dành cho tài khoản Giáo viên.")
        return super().dispatch(request, *args, **kwargs)


class ClassContextMixin(TeacherRequiredMixin):
    def get_class(self) -> TeacherClass:
        return get_object_or_404(TeacherClass, id=self.kwargs["cls_id"])

    def get_roster(self, cls):
        return (
            cls.roster
            .select_related("profile__user")
            .order_by("name", "profile__user__first_name", "id")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cls = self.get_class()
        ctx["cls"] = cls
        ctx["roster"] = list(self.get_roster(cls))
        ctx["title"] = f"{cls.name} – Giáo viên"
        ctx["active_tab"] = getattr(self, "active_tab", "students")
        return ctx


def _schedules_by_dow():
    """Return dict {dow_index: [ClassSchedule, ...]} for active classes."""
    by_dow = {}
    for s in (
        ClassSchedule.objects
        .filter(is_active=True, teacher_class__is_active=True)
        .select_related("teacher_class")
        .order_by("start_time")
    ):
        by_dow.setdefault(s.day_of_week, []).append(s)
    return by_dow


def _calendar_weeks(year, month):
    """Return list of weeks (each a list of day dicts) for given month."""
    import calendar as _cal
    today = timezone.localdate()
    by_dow = _schedules_by_dow()
    cal = _cal.Calendar(firstweekday=0)  # Mon
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        wrow = []
        for d in week:
            sessions = by_dow.get(d.weekday(), [])
            wrow.append({
                "date": d,
                "date_str": d.strftime("%Y-%m-%d"),
                "day_num": d.day,
                "sessions": sessions,
                "is_today": d == today,
                "is_outside": d.month != month,
                "is_past": d < today,
                "is_future": d > today,
            })
        weeks.append(wrow)
    return weeks


def _upcoming_sessions(limit=5):
    """Next `limit` sessions starting today (sorted by datetime)."""
    from datetime import timedelta
    today = timezone.localdate()
    by_dow = _schedules_by_dow()
    if not by_dow:
        return []
    # Notes lookup: {(cls_id, date): SessionNote}
    upcoming = []
    for delta in range(0, 60):
        if len(upcoming) >= limit:
            break
        d = today + timedelta(days=delta)
        for s in by_dow.get(d.weekday(), []):
            upcoming.append({"date": d, "schedule": s})
            if len(upcoming) >= limit:
                break
    # Fetch notes for these (cls, date) pairs
    pairs = [(u["schedule"].teacher_class_id, u["date"]) for u in upcoming]
    notes_map = {}
    if pairs:
        cls_ids = list({c for c, _ in pairs})
        dates = list({d for _, d in pairs})
        for n in SessionNote.objects.filter(teacher_class_id__in=cls_ids, date__in=dates):
            notes_map[(n.teacher_class_id, n.date)] = n
    for u in upcoming:
        u["note"] = notes_map.get((u["schedule"].teacher_class_id, u["date"]))
    return upcoming


class TeacherDashboard(TeacherRequiredMixin, TemplateView):
    template_name = "teacher/dashboard.html"

    def _month_param(self):
        from datetime import date as _date
        raw = self.request.GET.get("month")
        if raw:
            try:
                dt = datetime.strptime(raw + "-01", "%Y-%m-%d").date()
                return dt.year, dt.month
            except ValueError:
                pass
        t = timezone.localdate()
        return t.year, t.month

    def get_context_data(self, **kwargs):
        from datetime import date as _date
        ctx = super().get_context_data(**kwargs)
        classes = TeacherClass.objects.all().prefetch_related("roster")
        today = timezone.localdate()
        rows = []
        for cls in classes:
            paid = TuitionRecord.objects.filter(
                student__teacher_class=cls,
                period__year=today.year, period__month=today.month,
            ).aggregate(
                paid=Count("id", filter=Q(paid=True)),
                total=Count("id"),
            )
            rows.append({
                "cls": cls,
                "student_count": cls.roster.count(),
                "paid_count": paid["paid"] or 0,
                "tuition_total": paid["total"] or 0,
            })
        ctx["rows"] = rows
        ctx["title"] = "Dashboard giáo viên"

        # Calendar
        y, m = self._month_param()
        ctx["cal_weeks"] = _calendar_weeks(y, m)
        ctx["cal_year"], ctx["cal_month"] = y, m
        ctx["cal_label"] = _date(y, m, 1).strftime("%m/%Y")
        # Prev/next month
        prev_y, prev_m = (y, m - 1) if m > 1 else (y - 1, 12)
        next_y, next_m = (y, m + 1) if m < 12 else (y + 1, 1)
        ctx["prev_month"] = f"{prev_y:04d}-{prev_m:02d}"
        ctx["next_month"] = f"{next_y:04d}-{next_m:02d}"
        ctx["this_month"] = f"{today.year:04d}-{today.month:02d}"

        # Upcoming sessions (next 5 from today)
        ctx["upcoming"] = _upcoming_sessions(limit=5)
        return ctx


class ClassStudents(ClassContextMixin, TemplateView):
    template_name = "teacher/class_students.html"
    active_tab = "students"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cls = ctx["cls"]
        used_profile_ids = set(
            cls.roster.filter(profile__isnull=False).values_list("profile_id", flat=True)
        )
        ctx["available_profiles"] = (
            Profile.objects
            .exclude(id__in=used_profile_ids)
            .exclude(display_rank__in=("parent", "teacher"))
            .select_related("user")
            .order_by("user__first_name", "user__username")
        )
        return ctx


class ClassParents(ClassContextMixin, TemplateView):
    template_name = "teacher/class_parents.html"
    active_tab = "parents"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Cache eligible Profile picker (existing parent users / regular users)
        ctx["available_profiles"] = (
            Profile.objects
            .exclude(display_rank="teacher")
            .select_related("user")
            .order_by("user__first_name", "user__username")
        )
        # Group parent_contacts per student
        rows = []
        for s in ctx["roster"]:
            contacts = list(s.parent_contacts.select_related("profile__user"))
            rows.append({"student": s, "contacts": contacts})
        ctx["rows"] = rows
        return ctx


class ClassAttendance(ClassContextMixin, TemplateView):
    template_name = "teacher/class_attendance.html"
    active_tab = "attendance"

    def _lesson_dates(self, cls):
        """Return list of dates (past 4 weeks + next 1 week) matching
        the class's weekly schedule. Most recent first."""
        from datetime import timedelta
        schedules = list(ClassSchedule.objects.filter(teacher_class=cls, is_active=True))
        if not schedules:
            return [], {}
        # map day_of_week → list of ClassSchedule entries that day
        by_dow = {}
        for s in schedules:
            by_dow.setdefault(s.day_of_week, []).append(s)
        for k in by_dow:
            by_dow[k].sort(key=lambda x: x.start_time)
        today = timezone.localdate()
        dates = []
        for delta in range(-28, 8):
            d = today + timedelta(days=delta)
            if d.weekday() in by_dow:
                dates.append(d)
        dates.sort(reverse=True)
        return dates, by_dow

    def get_date(self, lesson_dates):
        raw = self.request.GET.get("date") or self.request.POST.get("date")
        if raw:
            try:
                return datetime.strptime(raw, "%Y-%m-%d").date()
            except ValueError:
                pass
        # Default to most recent past lesson day, or today if today is a lesson day
        today = timezone.localdate()
        if lesson_dates:
            past_or_today = [d for d in lesson_dates if d <= today]
            return past_or_today[0] if past_or_today else lesson_dates[-1]
        return today

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cls = ctx["cls"]
        lesson_dates, by_dow = self._lesson_dates(cls)
        d = self.get_date(lesson_dates)
        existing = {
            a.student_id: a
            for a in Attendance.objects.filter(student__teacher_class=cls, date=d)
        }
        rows = []
        for s in ctx["roster"]:
            a = existing.get(s.id)
            rows.append({
                "student": s,
                "present": a.present if a else False,
                "note": a.note if a else "",
            })
        today = timezone.localdate()
        ctx["date"] = d
        ctx["date_str"] = d.strftime("%Y-%m-%d")
        ctx["today"] = today
        ctx["rows"] = rows
        # Lesson session info for the selected date
        ctx["lessons_today"] = by_dow.get(d.weekday(), []) if by_dow else []
        ctx["is_lesson_day"] = bool(ctx["lessons_today"])
        ctx["has_schedule"] = bool(by_dow)
        # Pills: list of {date, label, is_selected, is_today, is_future}
        ctx["lesson_pills"] = [
            {
                "date": ld,
                "date_str": ld.strftime("%Y-%m-%d"),
                "label_day": ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][ld.weekday()],
                "label_date": ld.strftime("%d/%m"),
                "is_selected": ld == d,
                "is_today": ld == today,
                "is_future": ld > today,
            }
            for ld in lesson_dates
        ]
        return ctx


class ClassTuition(ClassContextMixin, TemplateView):
    template_name = "teacher/class_tuition.html"
    active_tab = "tuition"

    def get_period(self):
        raw = self.request.GET.get("period") or self.request.POST.get("period")
        if raw:
            try:
                return datetime.strptime(raw + "-01", "%Y-%m-%d").date()
            except ValueError:
                pass
        today = timezone.localdate()
        return date(today.year, today.month, 1)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        period = self.get_period()
        existing = {
            t.student_id: t
            for t in TuitionRecord.objects.filter(student__teacher_class=ctx["cls"], period=period)
        }
        rows = []
        paid_n = unpaid_n = 0
        for s in ctx["roster"]:
            t = existing.get(s.id)
            paid = t.paid if t else False
            amount = t.amount if t else 0
            if t:
                if paid: paid_n += 1
                else:    unpaid_n += 1
            rows.append({
                "student": s,
                "amount": amount,
                "paid": paid,
                "paid_at": t.paid_at if t else None,
                "note": t.note if t else "",
            })
        ctx["period"] = period
        ctx["period_str"] = period.strftime("%Y-%m")
        ctx["rows"] = rows
        ctx["paid_n"] = paid_n
        ctx["unpaid_n"] = unpaid_n
        return ctx


class ClassAcademic(ClassContextMixin, TemplateView):
    template_name = "teacher/class_academic.html"
    active_tab = "academic"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        latest = {}
        for ev in (
            AcademicLevel.objects
            .filter(student__teacher_class=ctx["cls"])
            .order_by("student_id", "-evaluated_at")
        ):
            latest.setdefault(ev.student_id, ev)
        rows = [{
            "student": s,
            "level": latest.get(s.id).level if s.id in latest else "",
            "level_display": latest.get(s.id).get_level_display() if s.id in latest else "",
            "evaluated_at": latest.get(s.id).evaluated_at if s.id in latest else None,
            "note": latest.get(s.id).note if s.id in latest else "",
        } for s in ctx["roster"]]
        ctx["rows"] = rows
        ctx["level_choices"] = ACADEMIC_LEVEL_CHOICES
        return ctx


class ClassScheduleView(ClassContextMixin, TemplateView):
    template_name = "teacher/class_schedule.html"
    active_tab = "schedule"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["schedules"] = list(
            ClassSchedule.objects.filter(teacher_class=ctx["cls"])
            .order_by("day_of_week", "start_time")
        )
        return ctx


class ClassRanking(ClassContextMixin, TemplateView):
    template_name = "teacher/class_ranking.html"
    active_tab = "ranking"

    def get_context_data(self, **kwargs):
        from judge.utils.parent import (
            get_class_ranking, current_week_start,
            get_class_daily_matrix, monday_of_week_for,
        )
        ctx = super().get_context_data(**kwargs)
        cls = ctx["cls"]
        ctx["ranking"] = get_class_ranking(cls.id)
        ctx["no_oj_count"] = cls.roster.filter(profile__isnull=True).count()
        ctx["summary"] = (
            ClassAISummary.objects.filter(teacher_class=cls)
            .order_by("-week_start").first()
        )
        ctx["current_week_start"] = current_week_start()

        # Daily-activity matrix with start/end range filter (default: this week).
        today = date.today()
        def _parse(name, fallback):
            raw = self.request.GET.get(name, "").strip()
            try:
                return datetime.strptime(raw, "%Y-%m-%d").date() if raw else fallback
            except ValueError:
                return fallback
        start = _parse("start", monday_of_week_for(today))
        end = _parse("end", today)
        if start > end:
            start, end = end, start
        # Cap the column count to keep the table readable / fast.
        if (end - start).days > 61:
            start = end - timedelta(days=61)
        ctx["matrix"] = get_class_daily_matrix(cls.id, start, end)
        ctx["range_start_iso"] = start.strftime("%Y-%m-%d")
        ctx["range_end_iso"] = end.strftime("%Y-%m-%d")
        ctx["today_iso"] = today.strftime("%Y-%m-%d")
        return ctx


def _require_teacher(request):
    prof = getattr(request, "profile", None)
    if not prof:
        return False
    return prof.is_teacher or request.user.is_staff


@require_POST
def regenerate_class_summary(request, cls_id):
    """Trigger AI summary ngay (nút 'Cập nhật ngay')."""
    if not _require_teacher(request):
        return HttpResponseForbidden()
    cls = get_object_or_404(TeacherClass, id=cls_id)
    from judge.utils.parent import generate_class_summary
    try:
        generate_class_summary(cls.id)
        messages.success(request, "Đã cập nhật tổng kết AI của lớp.")
    except Exception as e:  # noqa: BLE001
        messages.error(request, f"Không tạo được tổng kết AI: {e}")
    return HttpResponseRedirect(reverse("teacher_class_ranking", args=[cls_id]))


# ---------------------------------------------------------------------------
# Attendance / tuition / academic save
# ---------------------------------------------------------------------------
@require_POST
def save_attendance(request, cls_id):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    cls = get_object_or_404(TeacherClass, id=cls_id)
    try:
        d = datetime.strptime(request.POST["date"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return HttpResponseRedirect(reverse("teacher_class_attendance", args=[cls_id]))
    roster = list(cls.roster.all())
    present_ids = set(map(int, request.POST.getlist("present")))
    with transaction.atomic():
        for s in roster:
            note = request.POST.get(f"note_{s.id}", "").strip()
            Attendance.objects.update_or_create(
                student=s, date=d,
                defaults={"present": s.id in present_ids, "note": note},
            )
    messages.success(request, f"Đã lưu điểm danh ngày {d:%d/%m/%Y}.")
    return HttpResponseRedirect(
        f"{reverse('teacher_class_attendance', args=[cls_id])}?date={d:%Y-%m-%d}"
    )


@require_POST
def save_tuition(request, cls_id):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    cls = get_object_or_404(TeacherClass, id=cls_id)
    try:
        period = datetime.strptime(request.POST["period"] + "-01", "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return HttpResponseRedirect(reverse("teacher_class_tuition", args=[cls_id]))
    roster = list(cls.roster.all())
    paid_ids = set(map(int, request.POST.getlist("paid")))
    with transaction.atomic():
        for s in roster:
            amount_raw = request.POST.get(f"amount_{s.id}", "0")
            amount_digits = "".join(c for c in amount_raw if c.isdigit())
            try:
                amount = Decimal(amount_digits or "0")
            except InvalidOperation:
                amount = Decimal("0")
            note = request.POST.get(f"note_{s.id}", "").strip()
            is_paid = s.id in paid_ids
            row, _ = TuitionRecord.objects.update_or_create(
                student=s, period=period,
                defaults={"amount": amount, "note": note, "paid": is_paid},
            )
            if is_paid and not row.paid_at:
                row.paid_at = timezone.now()
                row.save(update_fields=["paid_at"])
            elif not is_paid and row.paid_at:
                row.paid_at = None
                row.save(update_fields=["paid_at"])
    messages.success(request, f"Đã lưu học phí kỳ {period:%m/%Y}.")
    return HttpResponseRedirect(
        f"{reverse('teacher_class_tuition', args=[cls_id])}?period={period:%Y-%m}"
    )


@require_POST
def save_academic(request, cls_id):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    cls = get_object_or_404(TeacherClass, id=cls_id)
    roster = list(cls.roster.all())
    valid_levels = {k for k, _ in ACADEMIC_LEVEL_CHOICES}
    with transaction.atomic():
        for s in roster:
            level = request.POST.get(f"level_{s.id}", "").strip()
            note = request.POST.get(f"note_{s.id}", "").strip()
            if not level or level not in valid_levels:
                continue
            latest = (
                AcademicLevel.objects
                .filter(student=s).order_by("-evaluated_at").first()
            )
            if latest and latest.level == level and latest.note == note:
                continue
            AcademicLevel.objects.create(student=s, level=level, note=note)
    messages.success(request, "Đã lưu đánh giá học lực.")
    return HttpResponseRedirect(reverse("teacher_class_academic", args=[cls_id]))


# ---------------------------------------------------------------------------
# Class CRUD
# ---------------------------------------------------------------------------
@require_POST
def create_class(request):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Cần nhập tên lớp.")
        return HttpResponseRedirect(reverse("teacher_home"))
    days = request.POST.getlist("day")
    starts = request.POST.getlist("start")
    ends = request.POST.getlist("end")
    subjects = request.POST.getlist("subject")
    teachers = request.POST.getlist("teacher")
    locations = request.POST.getlist("location")
    schedules_created = 0
    with transaction.atomic():
        cls = TeacherClass.objects.create(
            name=name[:200],
            short_name=request.POST.get("short_name", "").strip()[:50],
            description=request.POST.get("description", "").strip(),
        )
        for i in range(len(days)):
            d = days[i]; st = starts[i] if i < len(starts) else ""; et = ends[i] if i < len(ends) else ""
            subj = subjects[i] if i < len(subjects) else ""
            tch = teachers[i] if i < len(teachers) else ""
            loc = locations[i] if i < len(locations) else ""
            if not d or not st or not et or not subj.strip():
                continue
            try:
                ClassSchedule.objects.create(
                    teacher_class=cls, day_of_week=int(d),
                    start_time=st, end_time=et,
                    subject=subj.strip()[:200],
                    teacher=tch.strip()[:200],
                    location=loc.strip()[:200],
                )
                schedules_created += 1
            except (ValueError, TypeError):
                continue
    extra = f" + {schedules_created} buổi học" if schedules_created else ""
    messages.success(request, f"Đã tạo lớp {cls.name}{extra}.")
    return HttpResponseRedirect(reverse("teacher_class_students", args=[cls.id]))


@require_POST
def edit_class(request, cls_id):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    cls = get_object_or_404(TeacherClass, id=cls_id)
    name = request.POST.get("name", "").strip()
    if name:
        cls.name = name[:200]
    cls.short_name = request.POST.get("short_name", cls.short_name).strip()[:50]
    cls.description = request.POST.get("description", cls.description).strip()
    cls.is_active = bool(request.POST.get("is_active"))
    cls.save()
    messages.success(request, f"Đã cập nhật lớp {cls.name}.")
    return HttpResponseRedirect(reverse("teacher_class_students", args=[cls.id]))


@require_POST
def delete_class(request, cls_id):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    cls = get_object_or_404(TeacherClass, id=cls_id)
    name = cls.name
    cls.delete()
    messages.success(request, f"Đã xóa lớp {name}.")
    return HttpResponseRedirect(reverse("teacher_home"))


# ---------------------------------------------------------------------------
# Student CRUD
# ---------------------------------------------------------------------------
@require_POST
def add_student(request, cls_id):
    """Add a student to the class. Two modes:
       1. profile_id given → link to existing User/Profile.
       2. profile_id empty → create Student row with name + contact only.
    """
    if not _require_teacher(request):
        return HttpResponseForbidden()
    cls = get_object_or_404(TeacherClass, id=cls_id)
    profile_id_raw = request.POST.get("profile_id", "").strip()
    name = request.POST.get("name", "").strip()
    profile = None
    if profile_id_raw:
        try:
            profile = Profile.objects.get(id=int(profile_id_raw))
        except (ValueError, Profile.DoesNotExist):
            profile = None
    if not profile and not name:
        messages.error(request, "Cần chọn account OJ hoặc nhập họ tên.")
        return HttpResponseRedirect(reverse("teacher_class_students", args=[cls_id]))
    # Dedupe: skip if same profile already in roster
    if profile and Student.objects.filter(teacher_class=cls, profile=profile).exists():
        messages.warning(request, f"{profile.user.username} đã có trong lớp.")
        return HttpResponseRedirect(reverse("teacher_class_students", args=[cls_id]))
    s = Student.objects.create(
        teacher_class=cls,
        profile=profile,
        name=name[:200],
        phone=request.POST.get("phone", "").strip()[:30],
        zalo=request.POST.get("zalo", "").strip()[:50],
        facebook=request.POST.get("facebook", "").strip()[:255],
        grade=request.POST.get("grade", "").strip()[:50],
        school=request.POST.get("school", "").strip()[:255],
        note=request.POST.get("note", "").strip(),
    )
    label = profile.user.first_name or profile.user.username if profile else (name or "học sinh")
    messages.success(request, f"Đã thêm {label} vào lớp.")
    return HttpResponseRedirect(reverse("teacher_class_students", args=[cls_id]))


@require_POST
def save_student_info(request, cls_id):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    sid = request.POST.get("student_id")
    if not sid:
        return HttpResponseRedirect(reverse("teacher_class_students", args=[cls_id]))
    s = get_object_or_404(Student, id=int(sid))
    name = request.POST.get("name", "").strip()
    if name:
        s.name = name[:200]
    s.phone = request.POST.get("phone", s.phone).strip()[:30]
    s.zalo = request.POST.get("zalo", s.zalo).strip()[:50]
    s.facebook = request.POST.get("facebook", s.facebook).strip()[:255]
    s.grade = request.POST.get("grade", s.grade).strip()[:50]
    s.school = request.POST.get("school", s.school).strip()[:255]
    s.note = request.POST.get("note", s.note).strip()
    s.save()
    messages.success(request, f"Đã cập nhật {s.display_name}.")
    return HttpResponseRedirect(reverse("teacher_class_students", args=[cls_id]))


@require_POST
def remove_student(request, cls_id):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    sid = request.POST.get("student_id")
    if sid:
        try:
            s = Student.objects.get(id=int(sid))
            name = s.display_name
            s.delete()
            messages.success(request, f"Đã gỡ {name} khỏi lớp.")
        except Student.DoesNotExist:
            pass
    return HttpResponseRedirect(reverse("teacher_class_students", args=[cls_id]))


# ---------------------------------------------------------------------------
# Parent links — only meaningful for students with a Profile
# ---------------------------------------------------------------------------
@require_POST
def add_parent(request, cls_id):
    """Add a parent contact to a Student. Two modes:
       1. profile_id given → link to existing User/Profile (parent can login /parent/).
       2. profile_id empty → name-only contact, no OJ access.
    """
    if not _require_teacher(request):
        return HttpResponseForbidden()
    student_id = request.POST.get("student_id", "").strip()
    if not student_id:
        messages.error(request, "Cần chọn học sinh.")
        return HttpResponseRedirect(reverse("teacher_class_parents", args=[cls_id]))
    s = get_object_or_404(Student, id=int(student_id))

    profile_id_raw = request.POST.get("profile_id", "").strip()
    name = request.POST.get("name", "").strip()
    profile = None
    if profile_id_raw:
        try:
            profile = Profile.objects.get(id=int(profile_id_raw))
        except (ValueError, Profile.DoesNotExist):
            profile = None
    if not profile and not name:
        messages.error(request, "Cần chọn account OJ hoặc nhập họ tên phụ huynh.")
        return HttpResponseRedirect(reverse("teacher_class_parents", args=[cls_id]))
    if profile and ParentContact.objects.filter(student=s, profile=profile).exists():
        messages.warning(request, f"{profile.user.username} đã là phụ huynh của {s.display_name}.")
        return HttpResponseRedirect(reverse("teacher_class_parents", args=[cls_id]))

    pc = ParentContact.objects.create(
        student=s, profile=profile, name=name[:200],
        phone=request.POST.get("phone", "").strip()[:30],
        zalo=request.POST.get("zalo", "").strip()[:50],
        facebook=request.POST.get("facebook", "").strip()[:255],
        occupation=request.POST.get("occupation", "").strip()[:255],
        note=request.POST.get("note", "").strip(),
    )
    # If linked to a Profile + student has Profile → also wire up Profile.children
    # so the parent can login at /parent/ and see this child.
    if profile and s.profile_id:
        profile.display_rank = "parent"
        profile.save(update_fields=["display_rank"])
        profile.children.add(s.profile)

    messages.success(request, f"Đã thêm phụ huynh {pc.display_name} cho {s.display_name}.")
    return HttpResponseRedirect(reverse("teacher_class_parents", args=[cls_id]))


@require_POST
def save_parent_info(request, cls_id):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    pcid = request.POST.get("parent_contact_id")
    if not pcid:
        return HttpResponseRedirect(reverse("teacher_class_parents", args=[cls_id]))
    pc = get_object_or_404(ParentContact, id=int(pcid))
    name = request.POST.get("name", "").strip()
    if name:
        pc.name = name[:200]
    pc.phone = request.POST.get("phone", pc.phone).strip()[:30]
    pc.zalo = request.POST.get("zalo", pc.zalo).strip()[:50]
    pc.facebook = request.POST.get("facebook", pc.facebook).strip()[:255]
    pc.occupation = request.POST.get("occupation", pc.occupation).strip()[:255]
    pc.note = request.POST.get("note", pc.note).strip()
    pc.save()
    messages.success(request, f"Đã cập nhật phụ huynh {pc.display_name}.")
    return HttpResponseRedirect(reverse("teacher_class_parents", args=[cls_id]))


@require_POST
def remove_parent(request, cls_id):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    pcid = request.POST.get("parent_contact_id")
    if pcid:
        try:
            pc = ParentContact.objects.select_related("profile", "student__profile").get(id=int(pcid))
            label = pc.display_name
            # Also unlink Profile.children if both sides had Profile
            if pc.profile_id and pc.student.profile_id:
                pc.profile.children.remove(pc.student.profile)
            pc.delete()
            messages.success(request, f"Đã gỡ phụ huynh {label}.")
        except ParentContact.DoesNotExist:
            pass
    return HttpResponseRedirect(reverse("teacher_class_parents", args=[cls_id]))


@require_POST
def save_session_note(request):
    """Update/create a SessionNote for a given (teacher_class, date)."""
    if not _require_teacher(request):
        return HttpResponseForbidden()
    cls_id = request.POST.get("cls_id")
    date_raw = request.POST.get("date")
    content = request.POST.get("content", "").strip()
    if not cls_id or not date_raw:
        return HttpResponseRedirect(reverse("teacher_home"))
    cls = get_object_or_404(TeacherClass, id=int(cls_id))
    try:
        d = datetime.strptime(date_raw, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponseRedirect(reverse("teacher_home"))
    if content:
        SessionNote.objects.update_or_create(
            teacher_class=cls, date=d,
            defaults={"content": content},
        )
        messages.success(request, f"Đã lưu ghi chú cho {cls.name} – {d:%d/%m/%Y}.")
    else:
        # Empty content → delete note
        SessionNote.objects.filter(teacher_class=cls, date=d).delete()
        messages.success(request, f"Đã xóa ghi chú cho {cls.name} – {d:%d/%m/%Y}.")
    # Redirect back (preserve month query if present)
    nxt = request.POST.get("next") or reverse("teacher_home")
    return HttpResponseRedirect(nxt)


@require_POST
def save_schedule(request, cls_id):
    if not _require_teacher(request):
        return HttpResponseForbidden()
    cls = get_object_or_404(TeacherClass, id=cls_id)
    days = request.POST.getlist("day")
    starts = request.POST.getlist("start")
    ends = request.POST.getlist("end")
    subjects = request.POST.getlist("subject")
    teachers = request.POST.getlist("teacher")
    locations = request.POST.getlist("location")
    with transaction.atomic():
        ClassSchedule.objects.filter(teacher_class=cls).delete()
        for i in range(len(days)):
            d = days[i]; st = starts[i]; et = ends[i]
            subj = subjects[i] if i < len(subjects) else ""
            tch = teachers[i] if i < len(teachers) else ""
            loc = locations[i] if i < len(locations) else ""
            if not d or not st or not et or not subj.strip():
                continue
            try:
                ClassSchedule.objects.create(
                    teacher_class=cls, day_of_week=int(d),
                    start_time=st, end_time=et,
                    subject=subj.strip()[:200],
                    teacher=tch.strip()[:200],
                    location=loc.strip()[:200],
                )
            except (ValueError, TypeError):
                continue
    messages.success(request, "Đã lưu lịch học.")
    return HttpResponseRedirect(reverse("teacher_class_schedule", args=[cls_id]))
