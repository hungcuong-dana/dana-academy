from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("judge", "0254_coursejoinrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="courselessonproblem",
            name="section",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="problems",
                to="judge.courselessonsection",
                verbose_name="section",
                help_text="Section (chủ đề con) chứa bài tập này. Để trống = bài tập chung.",
            ),
        ),
    ]
