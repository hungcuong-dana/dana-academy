from django.contrib import admin


class TeacherClassAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "is_active", "student_count", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "short_name")
    ordering = ("-is_active", "name")

    def student_count(self, obj):
        return obj.roster.count()
    student_count.short_description = "HS"


class StudentAdmin(admin.ModelAdmin):
    list_display = ("display_name", "teacher_class", "username_or_no_account", "phone", "zalo", "school")
    list_filter = ("teacher_class",)
    search_fields = ("name", "profile__user__username", "phone", "school")
    autocomplete_fields = ("profile",)
    ordering = ("teacher_class", "name")

    def username_or_no_account(self, obj):
        return obj.profile.user.username if obj.profile_id else "(không OJ)"
    username_or_no_account.short_description = "Username"


class ParentContactAdmin(admin.ModelAdmin):
    list_display = ("display_name", "student", "username_or_no", "phone", "zalo", "occupation")
    list_filter = ("student__teacher_class",)
    search_fields = ("name", "profile__user__username", "phone", "student__name")
    autocomplete_fields = ("student", "profile")
    ordering = ("student",)

    def username_or_no(self, obj):
        return obj.profile.user.username if obj.profile_id else "(không OJ)"
    username_or_no.short_description = "Username"


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "present", "note", "recorded_at")
    list_filter = ("date", "present", "student__teacher_class")
    search_fields = ("student__name", "student__profile__user__username")
    autocomplete_fields = ("student",)
    date_hierarchy = "date"
    ordering = ("-date", "student_id")


class TuitionRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "period", "amount", "paid", "paid_at", "note")
    list_filter = ("paid", "period", "student__teacher_class")
    search_fields = ("student__name", "student__profile__user__username")
    autocomplete_fields = ("student",)
    date_hierarchy = "period"
    ordering = ("-period", "student_id")


class AcademicLevelAdmin(admin.ModelAdmin):
    list_display = ("student", "level", "evaluated_at")
    list_filter = ("level", "student__teacher_class")
    search_fields = ("student__name", "student__profile__user__username", "note")
    autocomplete_fields = ("student",)
    readonly_fields = ("evaluated_at",)
    ordering = ("-evaluated_at",)
