from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0001_initial'),
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceSession',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('date', models.DateField()),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'course',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='attendance_sessions',
                        to='courses.disciplina',
                    ),
                ),
                (
                    'created_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='attendance_sessions_created',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-date', '-id'],
                'unique_together': {('course', 'date')},
            },
        ),
        migrations.CreateModel(
            name='AttendanceRecord',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('P', 'Presente'),
                            ('A', 'Ausente'),
                            ('J', 'Justificado'),
                        ],
                        default='A',
                        max_length=1,
                    ),
                ),
                ('marked_at', models.DateTimeField(auto_now=True)),
                (
                    'marked_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='attendance_records_marked',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'session',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='records',
                        to='attendance.attendancesession',
                    ),
                ),
                (
                    'student',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='attendance_records',
                        to='students.student',
                    ),
                ),
            ],
            options={
                'ordering': ['student_id'],
                'unique_together': {('session', 'student')},
            },
        ),
    ]
