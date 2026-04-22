from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_preregistration'),
    ]

    operations = [
        migrations.AddField(
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
                max_length=2,
            ),
        ),
        migrations.AddField(
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
                max_length=2,
            ),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='pronouns',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
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
                max_length=3,
            ),
        ),
    ]
