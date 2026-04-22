from django.core.management.base import BaseCommand
from django.core import management
import os


class Command(BaseCommand):
    help = (
        'Tenta aplicar migrações do app courses com --fake-initial e '
        'carrega fixture de áreas e disciplinas'
    )

    def handle(self, *args, **options):
        self.stdout.write(
            'Tentando migrate --fake-initial para o app courses...'
        )
        try:
            management.call_command('migrate', 'courses', '--fake-initial')
            self.stdout.write(
                self.style.SUCCESS(
                    'migrate --fake-initial aplicado para courses '
                    '(se aplicável).'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f'migrate --fake-initial falhou: {e}'
                )
            )
            self.stdout.write(
                'Você pode tentar executar manualmente: '
                'python3 manage.py migrate courses --fake-initial'
            )

        self.stdout.write('Executando migrate normalmente...')
        try:
            management.call_command('migrate')
            self.stdout.write(
                self.style.SUCCESS('migrate aplicado com sucesso.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Erro ao executar migrate: {e}'
                )
            )
            self.stdout.write(
                'Se persistir, inspecione as migrations em courses/migrations '
                'e o arquivo db.sqlite3.'
            )
            return

        fixture_path = os.path.join(
            'courses', 'fixtures', 'initial_areas_disciplines.json'
        )
        if os.path.exists(fixture_path):
            self.stdout.write(
                'Carregando fixture initial_areas_disciplines.json...'
            )
            try:
                management.call_command('loaddata', fixture_path)
                self.stdout.write(
                    self.style.SUCCESS('Fixture carregada.')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Falha ao carregar fixture: {e}'
                    )
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Fixture não encontrada: {fixture_path}'
                )
            )

        self.stdout.write(self.style.SUCCESS('Concluído.'))
