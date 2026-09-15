import datetime

import pytest
from django.core.management import call_command
from django.utils import timezone

from tickets.factories import TicketFactory
from tickets.models import Status, Ticket


@pytest.mark.django_db
def test_closes_tickets_resolved_more_than_72h_ago():
    ticket = TicketFactory(status=Status.RESOLVIDO)
    Ticket.objects.filter(pk=ticket.pk).update(
        resolved_at=timezone.now() - datetime.timedelta(hours=73)
    )

    call_command("close_stale_tickets")

    ticket.refresh_from_db()
    assert ticket.status == Status.FECHADO
    assert ticket.closed_at is not None
    assert ticket.events.filter(field="status", to_value=Status.FECHADO).exists()


@pytest.mark.django_db
def test_does_not_close_recently_resolved_tickets():
    ticket = TicketFactory(status=Status.RESOLVIDO)
    Ticket.objects.filter(pk=ticket.pk).update(
        resolved_at=timezone.now() - datetime.timedelta(hours=10)
    )

    call_command("close_stale_tickets")

    ticket.refresh_from_db()
    assert ticket.status == Status.RESOLVIDO


@pytest.mark.django_db
def test_does_not_touch_tickets_in_other_statuses():
    ticket = TicketFactory(status=Status.EM_ANDAMENTO)

    call_command("close_stale_tickets")

    ticket.refresh_from_db()
    assert ticket.status == Status.EM_ANDAMENTO
