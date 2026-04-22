from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0002_preregistration_fields'),
    ]

    operations = [
        migrations.AddField(
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
                max_length=3,
            ),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='has_taken_enem',
            field=models.CharField(
                blank=True,
                choices=[('S', 'Sim'), ('N', 'Não')],
                max_length=1,
            ),
        ),
        migrations.AddField(
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
                max_length=4,
            ),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='has_internet_at_home',
            field=models.CharField(
                blank=True,
                choices=[('S', 'Sim'), ('N', 'Não')],
                max_length=1,
            ),
        ),
    ]
