from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("judge", "0249_parentcontact"),
    ]

    operations = [
        migrations.CreateModel(
            name="SessionNote",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(db_index=True, verbose_name="Ngày học")),
                ("content", models.TextField(blank=True, default="", verbose_name="Nội dung ghi chú")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("teacher_class", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="session_notes", to="judge.teacherclass", verbose_name="Lớp")),
            ],
            options={
                "verbose_name": "Ghi chú buổi học",
                "verbose_name_plural": "Ghi chú buổi học",
                "ordering": ("-date", "teacher_class_id"),
                "unique_together": {("teacher_class", "date")},
            },
        ),
    ]
