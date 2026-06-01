from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("judge", "0247_student"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="grade",
            field=models.CharField(
                blank=True, default="", max_length=50,
                help_text="VD: Lớp 8, Lớp 9, Lớp 10A1...",
                verbose_name="Lớp ở trường",
            ),
        ),
    ]
