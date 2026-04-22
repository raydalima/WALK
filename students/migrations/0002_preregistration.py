from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreRegistration',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    ),
                ),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150, blank=True)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=20, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
