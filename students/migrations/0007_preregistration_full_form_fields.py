from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0006_preregistration_add_missing_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='preregistration',
            name='social_name',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='birth_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='cpf',
            field=models.CharField(blank=True, default='', max_length=11),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='rg',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='address',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='city',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='state',
            field=models.CharField(blank=True, default='', max_length=2),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='zip_code',
            field=models.CharField(blank=True, default='', max_length=12),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='responsible_name',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='responsible_phone',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='graduation_year',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='intended_course',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='household_members',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='has_device',
            field=models.CharField(blank=True, default='', max_length=1),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='works_currently',
            field=models.CharField(blank=True, default='', max_length=1),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='how_did_you_hear',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='why_join',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='preregistration',
            name='consent',
            field=models.BooleanField(default=False),
        ),
    ]
