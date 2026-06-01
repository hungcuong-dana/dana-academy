from django.db import models
from django.utils.translation import gettext_lazy as _


class SubmissionAIScore(models.Model):
    """Computed AI-suspicion score for a submission. Admin-only view."""
    submission = models.OneToOneField(
        "judge.Submission",
        on_delete=models.CASCADE,
        related_name="ai_score",
        primary_key=True,
    )
    score = models.FloatField(default=0.0, db_index=True,
                              help_text=_("Combined 0-100, higher = more suspicious"))
    stylometry_score = models.FloatField(null=True, blank=True,
                                         help_text=_("0-100; null if no baseline yet"))
    markers_score = models.FloatField(default=0.0)
    markers_found = models.JSONField(default=list)
    baseline_size = models.IntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("AI suspicion score")
        verbose_name_plural = _("AI suspicion scores")
        ordering = ("-score",)
