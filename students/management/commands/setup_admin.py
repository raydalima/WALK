from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Aplica migrações (opcional) e cria ou atualiza um superuser.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Nome de usuário do superusuário')
        parser.add_argument('--email', default='admin@walk.com', help='E-mail do superusuário')
        parser.add_argument('--password', default=None, help='Senha do superuser')
        parser.add_argument('--no-migrate', action='store_true', dest='no_migrate', help='Pular migrações')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password'] or 'WALK123@'

        if not options.get('no_migrate'):
            self.stdout.write('Aplicando migrações...')
            call_command('migrate', interactive=False)

        User = get_user_model()
        user = User.objects.filter(username=username).first() or User.objects.filter(email=email).first()

        if user is None:
            self.stdout.write(f'Criando superuser {username}...')
            try:
                User.objects.create_superuser(username, email, password)
                self.stdout.write(self.style.SUCCESS('Superuser criado com sucesso.'))
            except TypeError:
                # modelo customizado que aceita argumentos diferentes
                User.objects.create_superuser(email=email, password=password)
                self.stdout.write(self.style.SUCCESS('Superuser criado com sucesso (modelo custom).'))
        else:
            self.stdout.write(f'Atualizando superuser {user}...')
            user.set_password(password)
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS('Superuser atualizado com sucesso.'))
