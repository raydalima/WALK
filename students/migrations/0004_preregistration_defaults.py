from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_preregistration_more_fields'),
    ]

    operations = [
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
            name='pronouns',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]
