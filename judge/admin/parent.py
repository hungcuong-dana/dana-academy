from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _, ngettext


class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "teacher_class",
        "day_of_week",
        "start_time",
        "end_time",
        "subject",
        "teacher",
        "location",
        "is_active",
    )
    list_filter = ("teacher_class", "day_of_week", "is_active")
    search_fields = ("teacher_class__name", "subject", "teacher")
    ordering = ("teacher_class", "day_of_week", "start_time")


class ChildAIAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "child",
        "week_start",
        "model_used",
        "prompt_tokens",
        "completion_tokens",
        "generated_at",
    )
    list_filter = ("week_start", "model_used")
    search_fields = ("child__user__username",)
    ordering = ("-week_start", "child__user__username")
    readonly_fields = ("generated_at", "model_used", "prompt_tokens", "completion_tokens")
    actions = ("regenerate_selected",)
    autocomplete_fields = ("child",)

    @admin.action(description=_("Regenerate selected assessments now"))
    def regenerate_selected(self, request, queryset):
        # Local import to avoid circulars at admin load time.
        from judge.utils.parent import generate_assessment

        ok, fail = 0, 0
        for row in queryset.select_related("child"):
            try:
                generate_assessment(row.child_id, force_week_start=row.week_start)
                ok += 1
            except Exception as e:
                fail += 1
                self.message_user(
                    request,
                    f"Failed for {row.child.username}: {e}",
                    level=messages.ERROR,
                )
        self.message_user(
            request,
            ngettext(
                "Regenerated %d assessment.",
                "Regenerated %d assessments.",
                ok,
            ) % ok,
            level=messages.SUCCESS if fail == 0 else messages.WARNING,
        )
