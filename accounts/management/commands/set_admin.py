from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Define is_staff e/ou is_superuser para um usuário identificado pelo e-mail.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='E-mail do usuário a atualizar')
        parser.add_argument('--staff', action='store_true', help='Marcar is_staff=True')
        parser.add_argument('--super', action='store_true', dest='superuser', help='Marcar is_superuser=True')
        parser.add_argument('--unset-staff', action='store_true', help='Definir is_staff=False')
        parser.add_argument('--unset-super', action='store_true', dest='unset_super', help='Definir is_superuser=False')

    def handle(self, *args, **options):
        email = options['email']
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'Usuário com e-mail {email} não encontrado')

        changed = False
        if options.get('staff'):
            user.is_staff = True
            changed = True
        if options.get('superuser'):
            user.is_superuser = True
            changed = True
        if options.get('unset_staff'):
            user.is_staff = False
            changed = True
        if options.get('unset_super'):
            user.is_superuser = False
            changed = True

        if changed:
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Usuário {email} atualizado: is_staff={user.is_staff}, is_superuser={user.is_superuser}'))
        else:
            self.stdout.write('Nenhuma alteração solicitada.')
