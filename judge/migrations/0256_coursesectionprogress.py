from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("judge", "0255_courselessonproblem_section"),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseSectionProgress",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("completed", models.BooleanField(default=False, verbose_name="completed")),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_progress",
                        to="judge.courselessonsection",
                        verbose_name="section",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="section_progress",
                        to="judge.profile",
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "section progress",
                "verbose_name_plural": "section progress",
                "unique_together": {("user", "section")},
            },
        ),
    ]
