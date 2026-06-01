from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("judge", "0246_teacherclass"),
    ]

    operations = [
        # 1. Drop old unique_together (refs teacher_class + student=Profile)
        migrations.AlterUniqueTogether(name="attendance", unique_together=set()),
        migrations.AlterUniqueTogether(name="tuitionrecord", unique_together=set()),
        # 2. Drop FKs (student=Profile, teacher_class) on Attendance/Tuition/Academic
        migrations.RemoveField(model_name="attendance", name="student"),
        migrations.RemoveField(model_name="attendance", name="teacher_class"),
        migrations.RemoveField(model_name="tuitionrecord", name="student"),
        migrations.RemoveField(model_name="tuitionrecord", name="teacher_class"),
        migrations.RemoveField(model_name="academiclevel", name="student"),
        migrations.RemoveField(model_name="academiclevel", name="teacher_class"),
        # 3. Drop TeacherClass.students M2M
        migrations.RemoveField(model_name="teacherclass", name="students"),
        # 4. Create Student model
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, default="", help_text="Bắt buộc nếu chưa có account OJ.", max_length=200, verbose_name="Họ tên")),
                ("phone", models.CharField(blank=True, default="", max_length=30, verbose_name="SĐT")),
                ("zalo", models.CharField(blank=True, default="", max_length=50, verbose_name="Zalo")),
                ("facebook", models.CharField(blank=True, default="", max_length=255, verbose_name="Facebook")),
                ("school", models.CharField(blank=True, default="", max_length=255, verbose_name="Trường")),
                ("note", models.TextField(blank=True, default="", verbose_name="Ghi chú")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("profile", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="student_records", to="judge.profile", verbose_name="Account OJ (tùy chọn)")),
                ("teacher_class", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="roster", to="judge.teacherclass", verbose_name="Lớp")),
            ],
            options={
                "verbose_name": "Học sinh",
                "verbose_name_plural": "Học sinh",
                "ordering": ("name", "id"),
            },
        ),
        # 5. Add new student FK on each tracker model
        migrations.AddField(
            model_name="attendance",
            name="student",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attendance_records",
                to="judge.student", verbose_name="Học sinh"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="tuitionrecord",
            name="student",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tuition_records",
                to="judge.student", verbose_name="Học sinh"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="academiclevel",
            name="student",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="academic_levels",
                to="judge.student", verbose_name="Học sinh"),
            preserve_default=False,
        ),
        # 6. Reinstate unique_together (now refs Student FK)
        migrations.AlterUniqueTogether(
            name="attendance", unique_together={("student", "date")},
        ),
        migrations.AlterUniqueTogether(
            name="tuitionrecord", unique_together={("student", "period")},
        ),
    ]
