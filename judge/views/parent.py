"""Parent Portal views.

Layout: parent users (Profile.display_rank == "parent") log in and are
redirected by DMOJLoginMiddleware to /parent/. This file ships the views
that power that section: dashboard listing children, per-child overview,
read-only submission/contest lists, and the AI weekly report viewer.
"""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from judge.models import (
    ChildAIAssessment,
    Problem,
    Profile,
    Submission,
)
from judge.utils.parent import (
    current_week_start,
    get_child_class_compare,
    get_child_contest_history,
    get_child_summary,
    get_display_name,
    get_heatmap,
    get_topic_breakdown,
    get_upcoming_contests,
)
from judge.utils.users import get_contest_ratings


class ParentRequiredMixin(LoginRequiredMixin):
    """Reject any request whose Profile is not display_rank='parent'."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.profile or not request.profile.is_parent:
            return HttpResponseForbidden(
                "Trang này chỉ dành cho tài khoản Phụ huynh."
            )
        return super().dispatch(request, *args, **kwargs)


class ChildAccessMixin(ParentRequiredMixin):
    """Resolve the child_id URL kwarg to a Profile, enforcing parent ownership."""

    def get_child(self) -> Profile:
        child_id = self.kwargs["child_id"]
        if not self.request.profile.children.filter(id=child_id).exists():
            raise PermissionDenied("Bạn không có quyền xem học sinh này.")
        return get_object_or_404(Profile.objects.select_related("user"), id=child_id)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        child = self.get_child()
        ctx["child"] = child
        ctx["child_display_name"] = get_display_name(child.user)
        ctx["child_summary"] = get_child_summary(child.id)
        ctx["title"] = f"{get_display_name(child.user)} – Theo dõi"
        return ctx


# --------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------
class ParentDashboard(ParentRequiredMixin, TemplateView):
    template_name = "parent/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        children = list(self.request.profile.children.select_related("user"))
        ctx["children"] = children
        ctx["children_summaries"] = [get_child_summary(c.id) for c in children]
        ctx["upcoming_contests"] = get_upcoming_contests(limit=3)
        ctx["parent_display_name"] = get_display_name(self.request.user)
        ctx["title"] = "Trang phụ huynh"
        return ctx


class ChildOverview(ChildAccessMixin, TemplateView):
    template_name = "parent/child_overview.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        child = ctx["child"]
        ctx["heatmap"] = get_heatmap(child.id)
        ctx["topic_breakdown"] = get_topic_breakdown(child.id)
        ctx["class_compare"] = get_child_class_compare(child.id)
        ctx["recent_submissions"] = (
            Submission.objects.filter(user=child)
            .select_related("problem", "language")
            .order_by("-date")[:10]
        )
        ctx["upcoming_contests"] = get_upcoming_contests(limit=3)
        ctx["recent_contest_participations"] = get_child_contest_history(child.id, limit=3)
        return ctx


class ChildSubmissions(ChildAccessMixin, TemplateView):
    template_name = "parent/child_submissions.html"

    PAGE_SIZE = 30

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        child = ctx["child"]
        page = max(int(self.request.GET.get("page", 1)), 1)
        offset = (page - 1) * self.PAGE_SIZE
        qs = (
            Submission.objects.filter(user=child)
            .select_related("problem", "language", "contest_object")
            .order_by("-date")
        )
        ctx["submissions"] = qs[offset : offset + self.PAGE_SIZE]
        ctx["page"] = page
        ctx["has_prev"] = page > 1
        ctx["has_next"] = qs.count() > offset + self.PAGE_SIZE
        return ctx


class ChildContests(ChildAccessMixin, TemplateView):
    template_name = "parent/child_contests.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        child = ctx["child"]
        ctx["contest_ratings"] = get_contest_ratings(child.id)
        ctx["upcoming_contests"] = get_upcoming_contests(limit=10)
        ctx["recent_contest_participations"] = get_child_contest_history(child.id, limit=20)
        return ctx


class ChildAIAssessmentView(ChildAccessMixin, TemplateView):
    template_name = "parent/child_ai.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        child = ctx["child"]
        latest = (
            ChildAIAssessment.objects.filter(child=child)
            .order_by("-week_start")
            .first()
        )
        ctx["assessment"] = latest
        if latest and latest.suggested_problem_codes:
            ctx["suggested_problems"] = list(
                Problem.objects.filter(code__in=latest.suggested_problem_codes)
            )
        else:
            ctx["suggested_problems"] = []
        ctx["next_run_week_start"] = current_week_start()
        return ctx
