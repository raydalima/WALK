from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        # Adiciona um modelo apenas no estado de migração chamado 'Course' que
        # funciona como um alias para 'Disciplina' (db_table existente: courses_disciplina).
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Course',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True,
                                                    primary_key=True,
                                                    serialize=False,
                                                    verbose_name='ID')),
                        ('nome', models.CharField(max_length=100)),
                        ('descricao', models.TextField(blank=True)),
                        ('icone', models.CharField(blank=True, max_length=50)),
                        ('area', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='disciplinas',
                            to='courses.areaconhecimento',
                        )),
                    ],
                    options={
                        'verbose_name': 'Course (alias)',
                        'verbose_name_plural': 'Courses (alias)',
                        'db_table': 'courses_disciplina',
                    },
                ),
            ],
        ),
    ]
