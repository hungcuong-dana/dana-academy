from django.contrib import admin
from django.urls import reverse_lazy
from django.forms import ModelForm

from judge.models import CourseRole
from judge.widgets import (
    AdminHeavySelect2MultipleWidget,
    AdminHeavySelect2Widget,
    HeavyPreviewAdminPageDownWidget,
    AdminSelect2Widget,
)


class CourseRoleInlineForm(ModelForm):
    class Meta:
        widgets = {
            "user": AdminHeavySelect2Widget(
                data_view="profile_select2", attrs={"style": "width: 100%"}
            ),
            "role": AdminSelect2Widget,
        }


class CourseRoleInline(admin.TabularInline):
    model = CourseRole
    extra = 1
    form = CourseRoleInlineForm


class CourseForm(ModelForm):
    class Meta:
        widgets = {
            "organizations": AdminHeavySelect2MultipleWidget(
                data_view="organization_select2"
            ),
            "about": HeavyPreviewAdminPageDownWidget(
                preview=reverse_lazy("blog_preview")
            ),
        }


class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        CourseRoleInline,
    ]
    list_display = ("name", "level", "rating", "is_public", "is_open")
    list_editable = ("rating",)
    search_fields = ("name",)
    form = CourseForm


class CourseLessonPrerequisiteAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "source_order",
        "target_order",
        "required_percentage",
    )
    list_filter = ("course",)
    search_fields = ("course__name",)
    ordering = ("course", "target_order", "source_order")


class CourseLessonProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "lesson",
        "is_unlocked",
        "percentage",
    )
    list_filter = ("is_unlocked", "lesson__course")
    search_fields = ("user__user__username", "lesson__title")
    ordering = ("lesson__course", "lesson__order", "user")
    raw_id_fields = ("user", "lesson")


class CourseLessonSectionAdmin(admin.ModelAdmin):
    list_display = ("lesson", "title", "order", "is_visible")
    list_filter = ("lesson__course", "is_visible")
    search_fields = ("title", "lesson__title", "lesson__course__name")
    ordering = ("lesson__course", "lesson__order", "order")
    raw_id_fields = ("lesson",)


class CourseJoinRequestAdmin(admin.ModelAdmin):
    list_display = ("course", "user", "created")
    list_filter = ("course",)
    search_fields = ("course__name", "user__user__username")
    ordering = ("course", "created")
    raw_id_fields = ("user",)


class CourseLessonProblemAdmin(admin.ModelAdmin):
    list_display = ("lesson", "section", "problem", "order", "score")
    list_filter = ("lesson__course",)
    search_fields = ("lesson__title", "problem__name", "problem__code")
    ordering = ("lesson__course", "lesson__order", "order")
    raw_id_fields = ("lesson", "problem", "section")


class CourseSectionProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "section", "completed", "updated")
    list_filter = ("completed", "section__lesson__course")
    search_fields = ("user__user__username", "section__title")
    raw_id_fields = ("user", "section")
