from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("judge", "0245_profile_facebook_profile_occupation_profile_phone_and_more"),
    ]

    operations = [
        # 1. New table: TeacherClass
        migrations.CreateModel(
            name="TeacherClass",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="Tên lớp")),
                ("short_name", models.CharField(blank=True, default="", max_length=50, verbose_name="Tên ngắn")),
                ("description", models.TextField(blank=True, default="", verbose_name="Mô tả")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Đang hoạt động")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("students", models.ManyToManyField(blank=True, related_name="teacher_classes", to="judge.profile", verbose_name="Học sinh")),
            ],
            options={
                "verbose_name": "Lớp học",
                "verbose_name_plural": "Lớp học",
                "ordering": ("-is_active", "name"),
            },
        ),
        # 2. Drop unique_together constraints first (they reference organization)
        migrations.AlterUniqueTogether(name="attendance", unique_together=set()),
        migrations.AlterUniqueTogether(name="tuitionrecord", unique_together=set()),
        # 3. Remove old organization FK fields
        migrations.RemoveField(model_name="attendance", name="organization"),
        migrations.RemoveField(model_name="tuitionrecord", name="organization"),
        migrations.RemoveField(model_name="academiclevel", name="organization"),
        migrations.RemoveField(model_name="classschedule", name="organization"),
        # 4. Add teacher_class FK on each
        migrations.AddField(
            model_name="attendance", name="teacher_class",
            field=models.ForeignKey(on_delete=models.deletion.CASCADE,
                                    related_name="attendance_records",
                                    to="judge.teacherclass", verbose_name="Lớp"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="tuitionrecord", name="teacher_class",
            field=models.ForeignKey(on_delete=models.deletion.CASCADE,
                                    related_name="tuition_records",
                                    to="judge.teacherclass", verbose_name="Lớp"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="academiclevel", name="teacher_class",
            field=models.ForeignKey(on_delete=models.deletion.CASCADE,
                                    related_name="academic_levels",
                                    to="judge.teacherclass", verbose_name="Lớp"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="classschedule", name="teacher_class",
            field=models.ForeignKey(on_delete=models.deletion.CASCADE,
                                    related_name="class_schedules",
                                    to="judge.teacherclass", verbose_name="Lớp"),
            preserve_default=False,
        ),
        # 5. Reinstate unique_together
        migrations.AlterUniqueTogether(
            name="attendance",
            unique_together={("student", "teacher_class", "date")},
        ),
        migrations.AlterUniqueTogether(
            name="tuitionrecord",
            unique_together={("student", "teacher_class", "period")},
        ),
    ]
