from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0007_preregistration_full_form_fields'),
    ]

    # Histórico legado: esta migration removia campos que não existem no
    # grafo consolidado atual, quebrando o carregamento das migrações.
    # Mantemos o arquivo como no-op para preservar a sequência histórica.
    operations = []
