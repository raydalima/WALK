from django.core.management.base import BaseCommand

from admin_panel.email_service import send_due_scheduled_communications


class Command(BaseCommand):
    help = 'Envia comunicações por e-mail que foram agendadas e já estão vencidas.'

    def handle(self, *args, **options):
        sent = send_due_scheduled_communications()
        self.stdout.write(self.style.SUCCESS(f'{len(sent)} comunicação(ões) agendada(s) processada(s).'))
