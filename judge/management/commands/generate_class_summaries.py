"""Cron-friendly command: weekly AI summary for every active teacher class.

Designed to run from crontab once a week (Sun 12:00). Idempotent for the
week containing the run date — repeated invocations skip classes that
already have a summary for that week unless --force is passed.

Usage:
    manage.py generate_class_summaries            # all active classes
    manage.py generate_class_summaries --class 2  # single class id
    manage.py generate_class_summaries --force    # regenerate this week
"""
from __future__ import annotations

import time

from django.core.management.base import BaseCommand

from judge.models import ClassAISummary, TeacherClass
from judge.utils.parent import current_week_start, generate_class_summary


class Command(BaseCommand):
    help = "Generate weekly AI summaries for teacher classes."

    def add_arguments(self, parser):
        parser.add_argument("--class", dest="cls", type=int, default=None,
                            help="Only process this single class id.")
        parser.add_argument("--force", action="store_true",
                            help="Regenerate even if a summary for this week exists.")
        parser.add_argument("--sleep", type=float, default=0.5,
                            help="Seconds to sleep between OpenAI calls.")

    def handle(self, *args, **opts):
        week_start = current_week_start()
        if opts["cls"]:
            class_ids = list(
                TeacherClass.objects.filter(id=opts["cls"]).values_list("id", flat=True)
            )
        else:
            class_ids = list(
                TeacherClass.objects.filter(is_active=True).values_list("id", flat=True)
            )
        self.stdout.write(f"Will process {len(class_ids)} class(es) for week {week_start}.")

        for cid in class_ids:
            if not opts["force"] and ClassAISummary.objects.filter(
                teacher_class_id=cid, week_start=week_start
            ).exists():
                self.stdout.write(f"Skip class {cid} (already done this week).")
                continue
            try:
                obj = generate_class_summary(cid)
                self.stdout.write(self.style.SUCCESS(
                    f"OK class={cid} tokens={obj.prompt_tokens}+{obj.completion_tokens}"
                ))
            except Exception as e:  # noqa: BLE001
                self.stderr.write(f"FAIL class={cid}: {e}")
            time.sleep(opts["sleep"])
