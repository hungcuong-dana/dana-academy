from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("judge", "0248_student_grade"),
    ]

    operations = [
        migrations.CreateModel(
            name="ParentContact",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, default="", help_text="Bắt buộc nếu chưa có account OJ.", max_length=200, verbose_name="Họ tên")),
                ("phone", models.CharField(blank=True, default="", max_length=30, verbose_name="SĐT")),
                ("zalo", models.CharField(blank=True, default="", max_length=50, verbose_name="Zalo")),
                ("facebook", models.CharField(blank=True, default="", max_length=255, verbose_name="Facebook")),
                ("occupation", models.CharField(blank=True, default="", max_length=255, verbose_name="Nghề nghiệp")),
                ("note", models.TextField(blank=True, default="", verbose_name="Ghi chú")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("profile", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="parent_contact_records", to="judge.profile", verbose_name="Account OJ (tùy chọn)")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="parent_contacts", to="judge.student", verbose_name="Học sinh")),
            ],
            options={
                "verbose_name": "Phụ huynh",
                "verbose_name_plural": "Phụ huynh",
                "ordering": ("student_id", "id"),
            },
        ),
    ]
