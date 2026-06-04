from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("judge", "0251_alter_tuitionrecord_period_classaisummary"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="level",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Optional billiards-style level label (e.g. K, C, B, A, H). Used to render the level roadmap on the course list.",
                max_length=8,
                verbose_name="skill level",
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="level_order",
            field=models.IntegerField(
                default=0,
                help_text="Sort position of this level in the roadmap (lower = earlier).",
                verbose_name="level order",
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="is_coming_soon",
            field=models.BooleanField(
                default=False,
                help_text="Show as a locked “coming soon” placeholder; the course cannot be opened or joined.",
                verbose_name="coming soon",
            ),
        ),
    ]
