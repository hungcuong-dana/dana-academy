from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("judge", "0252_course_level_coming_soon"),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseLessonSection",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="section title")),
                (
                    "theory",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Lý thuyết của section (markdown). Để trống nếu đang biên soạn.",
                        verbose_name="theory",
                    ),
                ),
                ("order", models.IntegerField(default=0, verbose_name="order")),
                ("is_visible", models.BooleanField(default=True, verbose_name="publicly visible")),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sections",
                        to="judge.courselesson",
                        verbose_name="lesson",
                    ),
                ),
            ],
            options={
                "verbose_name": "lesson section",
                "verbose_name_plural": "lesson sections",
                "ordering": ["order", "id"],
            },
        ),
    ]
