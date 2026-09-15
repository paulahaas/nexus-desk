import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import Status, Ticket
from tickets.services import transition_status

STALE_AFTER_HOURS = 72


class Command(BaseCommand):
    help = f"Fecha chamados RESOLVIDO há mais de {STALE_AFTER_HOURS}h sem reabertura."

    def handle(self, *args, **options):
        cutoff = timezone.now() - datetime.timedelta(hours=STALE_AFTER_HOURS)
        stale_tickets = Ticket.objects.filter(status=Status.RESOLVIDO, resolved_at__lte=cutoff)

        count = 0
        for ticket in stale_tickets:
            transition_status(ticket, Status.FECHADO, author=None)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"{count} chamado(s) fechado(s) automaticamente."))
