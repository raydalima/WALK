from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('students', '0009_merge_20260408_1145'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='approved_course',
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name='Curso em que foi aprovado',
            ),
        ),
        migrations.AddField(
            model_name='student',
            name='exit_reason',
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name='Motivo de saída',
            ),
        ),
        migrations.AddField(
            model_name='student',
            name='status',
            field=models.CharField(
                choices=[
                    ('CURSANDO', 'Cursando'),
                    ('APROVADO', 'Aprovado'),
                    ('INATIVO', 'Inativo'),
                    ('EVADIDO', 'Evadido'),
                ],
                default='CURSANDO',
                max_length=20,
                verbose_name='Situação Acadêmica',
            ),
        ),
        migrations.CreateModel(
            name='StudentHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120, verbose_name='Título')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='student_history_entries',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Registrado por',
                    ),
                ),
                (
                    'student',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='history_entries',
                        to='students.student',
                        verbose_name='Aluno',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Histórico do Aluno',
                'verbose_name_plural': 'Históricos dos Alunos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.RenameField(
            model_name='preregistration',
            old_name='first_name',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='preregistration',
            old_name='racial_self_declaration',
            new_name='race_self_declaration',
        ),
        migrations.RenameField(
            model_name='preregistration',
            old_name='school_status',
            new_name='school_situation',
        ),
        migrations.RenameField(
            model_name='preregistration',
            old_name='family_income',
            new_name='family_income_range',
        ),
        migrations.RenameField(
            model_name='preregistration',
            old_name='has_internet',
            new_name='has_internet_at_home',
        ),
        migrations.RenameField(
            model_name='preregistration',
            old_name='previous_vesting',
            new_name='has_taken_enem',
        ),
        migrations.AddField(
            model_name='preregistration',
            name='responsible_address',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='responsible_cpf',
            field=models.CharField(blank=True, default='', max_length=11),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='responsible_relationship',
            field=models.CharField(
                blank=True,
                choices=[
                    ('MAE', 'Mãe'),
                    ('PAI', 'Pai'),
                    ('RES', 'Responsável'),
                    ('OUT', 'Outro'),
                ],
                default='',
                max_length=3,
            ),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='responsible_relationship_other',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='responsible_rg',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='cpf',
            field=models.CharField(blank=True, default='', max_length=11),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='family_income_range',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ATE1', 'Até 1 salário mínimo'),
                    ('1A2', 'De 1 a 2 salários mínimos'),
                    ('2A3', 'De 2 a 3 salários mínimos'),
                    ('3A5', 'De 3 a 5 salários mínimos'),
                    ('A5', 'Acima de 5 salários mínimos'),
                    ('NI', 'Prefiro não informar'),
                ],
                default='',
                max_length=4,
            ),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[
                    ('F', 'Feminino'),
                    ('M', 'Masculino'),
                    ('NB', 'Não-binário'),
                    ('O', 'Outro'),
                    ('NI', 'Prefiro não informar'),
                ],
                default='',
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='graduation_year',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='has_device',
            field=models.CharField(
                blank=True,
                choices=[('S', 'Sim'), ('N', 'Não')],
                default='',
                max_length=1,
            ),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='has_internet_at_home',
            field=models.CharField(
                blank=True,
                choices=[('S', 'Sim'), ('N', 'Não')],
                default='',
                max_length=1,
            ),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='has_taken_enem',
            field=models.CharField(
                blank=True,
                choices=[('S', 'Sim'), ('N', 'Não')],
                default='',
                max_length=1,
            ),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='household_members',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='intended_course',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='phone',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='pronouns',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='race_self_declaration',
            field=models.CharField(
                blank=True,
                choices=[
                    ('BR', 'Branca'),
                    ('PR', 'Preta'),
                    ('PA', 'Parda'),
                    ('AM', 'Amarela'),
                    ('IN', 'Indígena'),
                    ('ND', 'Prefiro não declarar'),
                ],
                default='',
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='rg',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='school_situation',
            field=models.CharField(
                blank=True,
                choices=[
                    ('CUR', 'Cursando'),
                    ('CON', 'Concluído'),
                    ('TRA', 'Trancado/Interrompido'),
                    ('OUT', 'Outro'),
                ],
                default='',
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='school_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('PUB', 'Pública'),
                    ('PRI', 'Privada'),
                    ('MIS', 'Mista'),
                    ('NI', 'Prefiro não informar'),
                ],
                default='',
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='state',
            field=models.CharField(blank=True, default='', max_length=2),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='works_currently',
            field=models.CharField(
                blank=True,
                choices=[('S', 'Sim'), ('N', 'Não')],
                default='',
                max_length=1,
            ),
        ),
        migrations.AlterField(
            model_name='preregistration',
            name='zip_code',
            field=models.CharField(blank=True, default='', max_length=12),
        ),
    ]
