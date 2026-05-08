"""Cron-friendly command: weekly AI assessment for every student that has
at least one parent profile linked via Profile.children M2M.

Designed to run from crontab once a week (Sun 12:00). Idempotent for the
ISO week containing the run date — repeated invocations skip rows that
already exist for that week unless --force is passed.

Usage:
    manage.py generate_parent_assessments              # all eligible children
    manage.py generate_parent_assessments --child 42   # single child id
    manage.py generate_parent_assessments --force      # regenerate this week
"""
from __future__ import annotations

import time

from django.core.management.base import BaseCommand

from judge.models import ChildAIAssessment, Profile
from judge.utils.parent import current_week_start, generate_assessment


class Command(BaseCommand):
    help = "Generate weekly AI assessments for children that have at least one parent."

    def add_arguments(self, parser):
        parser.add_argument(
            "--child", type=int, default=None,
            help="Only process this single child profile id.",
        )
        parser.add_argument(
            "--force", action="store_true",
            help="Regenerate even if an assessment for the current week exists.",
        )
        parser.add_argument(
            "--sleep", type=float, default=0.5,
            help="Seconds to sleep between OpenAI calls (rate-limit cushion).",
        )

    def handle(self, *args, **opts):
        week_start = current_week_start()

        if opts["child"]:
            qs = Profile.objects.filter(id=opts["child"])
            if not opts["force"] and not qs.filter(parents__isnull=False).exists():
                self.stderr.write(
                    f"Profile {opts['child']} has no parents linked; "
                    f"pass --force to override."
                )
                return
            child_ids = list(qs.values_list("id", flat=True))
        else:
            # CHỈ học sinh có ít nhất 1 parent qua M2M reverse Profile.children → parents.
            child_ids = list(
                Profile.objects
                .filter(parents__isnull=False)
                .values_list("id", flat=True)
                .distinct()
            )

        if not child_ids:
            self.stdout.write("No eligible children — nothing to do.")
            return

        self.stdout.write(
            f"Processing {len(child_ids)} children for week starting "
            f"{week_start.strftime('%Y-%m-%d')}."
        )

        ok = 0
        skipped = 0
        failed = 0
        for cid in child_ids:
            existing = ChildAIAssessment.objects.filter(
                child_id=cid, week_start=week_start
            ).first()
            if existing and not opts["force"]:
                self.stdout.write(f"  skip child={cid} (already done this week)")
                skipped += 1
                continue
            try:
                row = generate_assessment(cid, force_week_start=week_start)
                self.stdout.write(
                    f"  ok   child={cid} model={row.model_used} "
                    f"tokens={row.prompt_tokens}+{row.completion_tokens}"
                )
                ok += 1
            except Exception as exc:
                self.stderr.write(f"  fail child={cid}: {exc}")
                failed += 1
            if opts["sleep"]:
                time.sleep(opts["sleep"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. ok={ok} skipped={skipped} failed={failed}"
            )
        )
