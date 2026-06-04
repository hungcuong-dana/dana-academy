from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("judge", "0253_courselessonsection"),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseJoinRequest",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True, verbose_name="requested at")),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="join_requests",
                        to="judge.course",
                        verbose_name="course",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="course_join_requests",
                        to="judge.profile",
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "course join request",
                "verbose_name_plural": "course join requests",
                "ordering": ["created"],
                "unique_together": {("course", "user")},
            },
        ),
    ]
