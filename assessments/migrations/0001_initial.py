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
            name='Quiz',
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
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('is_published', models.BooleanField(default=False)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'course',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='quizzes',
                        to='courses.disciplina',
                    ),
                ),
                (
                    'created_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='created_quizzes',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Question',
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
                ('text', models.TextField()),
                (
                    'type',
                    models.CharField(
                        choices=[
                            ('MCQ', 'Múltipla escolha'),
                            ('TF', 'Verdadeiro/Falso'),
                            ('ST', 'Resposta curta'),
                            ('ES', 'Redação/Discursiva'),
                        ],
                        default='MCQ',
                        max_length=3,
                    ),
                ),
                ('order', models.PositiveIntegerField(default=0)),
                (
                    'points',
                    models.DecimalField(
                        decimal_places=2,
                        default=1,
                        max_digits=6,
                    ),
                ),
                ('correct_text', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'quiz',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='questions',
                        to='assessments.quiz',
                    ),
                ),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Choice',
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
                ('text', models.CharField(max_length=300)),
                ('is_correct', models.BooleanField(default=False)),
                (
                    'question',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='choices',
                        to='assessments.question',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
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
                ('attempt', models.PositiveIntegerField(default=1)),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('DRAFT', 'Rascunho'),
                            ('SUB', 'Enviado'),
                            ('GRD', 'Corrigido'),
                        ],
                        default='DRAFT',
                        max_length=5,
                    ),
                ),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('corrected_at', models.DateTimeField(blank=True, null=True)),
                (
                    'corrected_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='corrected_submissions',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'quiz',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='submissions',
                        to='assessments.quiz',
                    ),
                ),
                (
                    'student',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='quiz_submissions',
                        to='students.student',
                    ),
                ),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='Answer',
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
                ('text_answer', models.TextField(blank=True)),
                (
                    'auto_score',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=6,
                        null=True,
                    ),
                ),
                (
                    'teacher_score',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=6,
                        null=True,
                    ),
                ),
                ('teacher_feedback', models.TextField(blank=True)),
                (
                    'question',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='answers',
                        to='assessments.question',
                    ),
                ),
                (
                    'selected_choice',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='+',
                        to='assessments.choice',
                    ),
                ),
                (
                    'submission',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='answers',
                        to='assessments.submission',
                    ),
                ),
            ],
            options={
                'unique_together': {('submission', 'question')},
            },
        ),
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(
                fields=['quiz', 'student', 'attempt'],
                name='assessments__quiz_id_0b0e2d_idx',
            ),
        ),
    ]
