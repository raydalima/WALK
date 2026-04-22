from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = 'Define uma senha temporária igual para todos os usuários em ambiente local.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            required=True,
            help='Senha temporária que será aplicada a todos os usuários.',
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                'Este comando só pode ser executado com DEBUG=True.'
            )

        password = options['password'].strip()
        if len(password) < 8:
            raise CommandError('Use uma senha com pelo menos 8 caracteres.')

        users = User.objects.all()
        total = users.count()

        for user in users.iterator():
            user.set_password(password)
            user.save(update_fields=['password'])

        self.stdout.write(
            self.style.SUCCESS(
                f'Senha temporária atualizada para {total} usuário(s).'
            )
        )
