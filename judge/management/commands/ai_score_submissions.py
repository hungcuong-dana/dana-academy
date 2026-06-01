"""Compute AI suspicion score for submissions.

Usage:
  python manage.py ai_score_submissions              # score all submissions missing a score
  python manage.py ai_score_submissions --contest lqdbrvt2026
  python manage.py ai_score_submissions --recent 100
  python manage.py ai_score_submissions --recompute  # re-score even if already scored
"""
from django.core.management.base import BaseCommand
from judge.models import Submission, SubmissionAIScore, Contest
from judge.utils.ai_detect import compute_ai_score


class Command(BaseCommand):
    help = "Compute AI-suspicion scores for submissions."

    def add_arguments(self, parser):
        parser.add_argument("--contest", type=str, help="Limit to contest key")
        parser.add_argument("--user", type=str, help="Limit to one username")
        parser.add_argument("--recent", type=int, help="Last N submissions")
        parser.add_argument("--recompute", action="store_true",
                            help="Re-score even if already scored")

    def handle(self, *args, **opts):
        qs = (Submission.objects
              .filter(language__key__in=["C", "CPP03", "CPP11", "CPP14", "CPP17", "CPP20"])
              .order_by("-id"))
        if opts.get("contest"):
            c = Contest.objects.get(key=opts["contest"])
            qs = qs.filter(contest_object=c)
        if opts.get("user"):
            qs = qs.filter(user__user__username=opts["user"])
        if not opts.get("recompute"):
            qs = qs.exclude(ai_score__isnull=False)
        if opts.get("recent"):
            qs = qs[:opts["recent"]]

        total = qs.count() if not opts.get("recent") else min(qs.count(), opts["recent"])
        self.stdout.write(f"Scoring {total} submissions...")
        n_done = 0
        for sub in qs.iterator(chunk_size=50):
            try:
                result = compute_ai_score(sub)
                SubmissionAIScore.objects.update_or_create(
                    submission=sub,
                    defaults={
                        "score": result["score"],
                        "stylometry_score": result["stylometry"],
                        "markers_score": result["markers_score"],
                        "markers_found": result["markers_found"],
                        "baseline_size": result["baseline_size"],
                    },
                )
                n_done += 1
                if n_done % 50 == 0:
                    self.stdout.write(f"  ... {n_done}/{total}")
            except Exception as e:
                self.stderr.write(f"FAIL sub#{sub.id}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Done. Scored {n_done} submissions."))
