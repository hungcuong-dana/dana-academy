from django.db import models
from django.utils.translation import gettext_lazy as _

from judge.models.profile import Profile


__all__ = ["TeacherClass", "Student", "ParentContact", "SessionNote",
           "Attendance", "TuitionRecord", "AcademicLevel", "ClassAISummary"]


class TeacherClass(models.Model):
    """Lớp học do giáo viên quản lý — độc lập với Organization (group OJ)."""
    name = models.CharField(max_length=200, verbose_name=_("Tên lớp"))
    short_name = models.CharField(max_length=50, blank=True, default="",
                                  verbose_name=_("Tên ngắn"))
    description = models.TextField(blank=True, default="",
                                   verbose_name=_("Mô tả"))
    is_active = models.BooleanField(default=True, db_index=True,
                                    verbose_name=_("Đang hoạt động"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-is_active", "name")
        verbose_name = _("Lớp học")
        verbose_name_plural = _("Lớp học")

    def __str__(self):
        return self.name


class Student(models.Model):
    """Một học sinh trong lớp.

    `profile` là FK *tùy chọn* tới Profile (= account OJ). Học sinh không
    có account OJ vẫn được track điểm danh / học phí / học lực — chỉ
    không xuất hiện ở các page OJ và không liên kết được với phụ huynh.
    """
    teacher_class = models.ForeignKey(
        TeacherClass, on_delete=models.CASCADE,
        related_name="roster", verbose_name=_("Lớp"),
    )
    profile = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="student_records",
        verbose_name=_("Account OJ (tùy chọn)"),
    )
    name = models.CharField(
        max_length=200, blank=True, default="",
        verbose_name=_("Họ tên"),
        help_text=_("Bắt buộc nếu chưa có account OJ."),
    )
    phone = models.CharField(max_length=30, blank=True, default="", verbose_name=_("SĐT"))
    zalo = models.CharField(max_length=50, blank=True, default="", verbose_name=_("Zalo"))
    facebook = models.CharField(max_length=255, blank=True, default="", verbose_name=_("Facebook"))
    grade = models.CharField(
        max_length=50, blank=True, default="",
        verbose_name=_("Lớp ở trường"),
        help_text=_("VD: Lớp 8, Lớp 9, Lớp 10A1..."),
    )
    school = models.CharField(max_length=255, blank=True, default="", verbose_name=_("Trường"))
    note = models.TextField(blank=True, default="", verbose_name=_("Ghi chú"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name", "id")
        verbose_name = _("Học sinh")
        verbose_name_plural = _("Học sinh")

    @property
    def display_name(self) -> str:
        if self.profile_id and self.profile.user.first_name:
            return self.profile.user.first_name
        if self.name:
            return self.name
        if self.profile_id:
            return self.profile.user.username
        return "(chưa đặt tên)"

    @property
    def username(self) -> str:
        return self.profile.user.username if self.profile_id else ""

    def __str__(self):
        return f"{self.display_name} @ {self.teacher_class.name}"


class ParentContact(models.Model):
    """Thông tin phụ huynh của một học sinh trong lớp.

    `profile` là FK *tùy chọn* tới Profile (= account OJ). Phụ huynh có
    Profile sẽ login được /parent/ để xem tiến độ con; phụ huynh không
    OJ chỉ có thông tin liên hệ để giáo viên gọi/nhắn.
    """
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE,
        related_name="parent_contacts", verbose_name=_("Học sinh"),
    )
    profile = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="parent_contact_records",
        verbose_name=_("Account OJ (tùy chọn)"),
    )
    name = models.CharField(
        max_length=200, blank=True, default="",
        verbose_name=_("Họ tên"),
        help_text=_("Bắt buộc nếu chưa có account OJ."),
    )
    phone = models.CharField(max_length=30, blank=True, default="", verbose_name=_("SĐT"))
    zalo = models.CharField(max_length=50, blank=True, default="", verbose_name=_("Zalo"))
    facebook = models.CharField(max_length=255, blank=True, default="", verbose_name=_("Facebook"))
    occupation = models.CharField(max_length=255, blank=True, default="", verbose_name=_("Nghề nghiệp"))
    note = models.TextField(blank=True, default="", verbose_name=_("Ghi chú"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("student_id", "id")
        verbose_name = _("Phụ huynh")
        verbose_name_plural = _("Phụ huynh")

    @property
    def display_name(self) -> str:
        if self.profile_id and self.profile.user.first_name:
            return self.profile.user.first_name
        if self.name:
            return self.name
        if self.profile_id:
            return self.profile.user.username
        return "(chưa đặt tên)"

    @property
    def username(self) -> str:
        return self.profile.user.username if self.profile_id else ""

    def __str__(self):
        return f"PH của {self.student.display_name}: {self.display_name}"


class SessionNote(models.Model):
    """Ghi chú cho 1 buổi học cụ thể của 1 lớp.

    Dùng để GV note trước nội dung sẽ dạy / kiểm tra / nhắc nhở cho buổi
    sắp tới (vd: "Kiểm tra 15 phút bài Mảng 2 chiều"). Hiển thị trên
    dashboard ở khu vực "Buổi học sắp tới".
    """
    teacher_class = models.ForeignKey(
        TeacherClass, on_delete=models.CASCADE,
        related_name="session_notes", verbose_name=_("Lớp"),
    )
    date = models.DateField(db_index=True, verbose_name=_("Ngày học"))
    content = models.TextField(blank=True, default="", verbose_name=_("Nội dung ghi chú"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("teacher_class", "date")
        ordering = ("-date", "teacher_class_id")
        verbose_name = _("Ghi chú buổi học")
        verbose_name_plural = _("Ghi chú buổi học")

    def __str__(self):
        return f"{self.teacher_class.name} – {self.date}"


ACADEMIC_LEVEL_CHOICES = (
    ("yeu",       _("Yếu")),
    ("tb",        _("Trung bình")),
    ("kha",       _("Khá")),
    ("tot",       _("Tốt")),
    ("xuat_sac",  _("Xuất sắc")),
)


class Attendance(models.Model):
    """Một dòng = 1 học sinh / 1 buổi học. Tick `present` để điểm danh."""
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="attendance_records",
        verbose_name=_("Học sinh"),
    )
    date = models.DateField(db_index=True, verbose_name=_("Ngày học"))
    present = models.BooleanField(default=False, verbose_name=_("Có mặt"))
    note = models.CharField(max_length=255, blank=True, verbose_name=_("Ghi chú"))
    recorded_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "date")
        ordering = ("-date", "student_id")
        verbose_name = _("Điểm danh")
        verbose_name_plural = _("Điểm danh")

    def __str__(self):
        return f"{self.student.display_name} – {self.date}"


class TuitionRecord(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="tuition_records",
        verbose_name=_("Học sinh"),
    )
    period = models.DateField(
        db_index=True, verbose_name=_("Kỳ học phí"),
        help_text=_("Ngày đầu tháng (vd 2026-05-01)."),
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=0, default=0,
        verbose_name=_("Học phí (VNĐ)"),
    )
    paid = models.BooleanField(default=False, db_index=True, verbose_name=_("Đã đóng"))
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Thời gian đóng"))
    note = models.CharField(max_length=255, blank=True, verbose_name=_("Ghi chú"))

    class Meta:
        unique_together = ("student", "period")
        ordering = ("-period", "student_id")
        verbose_name = _("Học phí")
        verbose_name_plural = _("Học phí")

    def __str__(self):
        return f"{self.student.display_name} – {self.period:%m/%Y} – {self.amount:,.0f}đ"


class AcademicLevel(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="academic_levels",
        verbose_name=_("Học sinh"),
    )
    level = models.CharField(
        max_length=10, choices=ACADEMIC_LEVEL_CHOICES,
        verbose_name=_("Học lực"),
    )
    evaluated_at = models.DateTimeField(auto_now_add=True, db_index=True,
                                        verbose_name=_("Thời điểm đánh giá"))
    note = models.TextField(blank=True, verbose_name=_("Ghi chú"))

    class Meta:
        ordering = ("-evaluated_at",)
        verbose_name = _("Học lực")
        verbose_name_plural = _("Học lực")

    def __str__(self):
        return f"{self.student.display_name} – {self.get_level_display()}"


class ClassAISummary(models.Model):
    """Báo cáo AI tổng quan lớp học, sinh hàng tuần (Chủ Nhật). 1 row/(lớp, tuần)."""
    teacher_class = models.ForeignKey(
        TeacherClass, on_delete=models.CASCADE, related_name="ai_summaries",
        verbose_name=_("Lớp"),
    )
    week_start = models.DateField(db_index=True, verbose_name=_("Tuần (thứ Hai)"))
    generated_at = models.DateTimeField(auto_now=True, db_index=True,
                                        verbose_name=_("Sinh lúc"))
    markdown = models.TextField(verbose_name=_("Nội dung (Markdown)"))
    model_used = models.CharField(max_length=64, blank=True, default="")
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)

    class Meta:
        unique_together = ("teacher_class", "week_start")
        ordering = ("-week_start",)
        verbose_name = _("Tổng kết AI của lớp")
        verbose_name_plural = _("Tổng kết AI của lớp")

    def __str__(self):
        return f"{self.teacher_class.name} – tuần {self.week_start}"
