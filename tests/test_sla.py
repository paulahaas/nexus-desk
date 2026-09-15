import datetime

import pytest
from django.utils import timezone

from tickets.factories import TicketFactory
from tickets.models import BusinessHours, Holiday, Priority, SLAPolicy, Status, Ticket, TicketEvent
from tickets.sla import (
    SLAState,
    add_business_minutes,
    business_minutes_between,
    first_response_sla,
    resolution_sla,
)

# ISO 8601: dia 1 da semana ISO é sempre segunda-feira, independente do ano.
MONDAY = datetime.date.fromisocalendar(2026, 2, 1)
TUESDAY = MONDAY + datetime.timedelta(days=1)
WEDNESDAY = MONDAY + datetime.timedelta(days=2)
FRIDAY = MONDAY + datetime.timedelta(days=4)
NEXT_MONDAY = MONDAY + datetime.timedelta(days=7)


def dt(date, hour, minute=0):
    return timezone.make_aware(datetime.datetime.combine(date, datetime.time(hour, minute)))


def _set_created_at(ticket, when):
    Ticket.objects.filter(pk=ticket.pk).update(created_at=when)
    ticket.refresh_from_db()


def _add_status_event(ticket, status, at, *, ticket_status=None):
    """Registra um TicketEvent de status com timestamp controlado (pra simular histórico)."""
    event = TicketEvent.objects.create(
        ticket=ticket, field="status", from_value=ticket.status, to_value=status
    )
    TicketEvent.objects.filter(pk=event.pk).update(created_at=at)
    ticket.status = ticket_status or status
    ticket.save(update_fields=["status"])
    ticket.refresh_from_db()


@pytest.fixture
def business_hours(db):
    for weekday in range(5):
        BusinessHours.objects.create(
            weekday=weekday, start_time=datetime.time(8, 0), end_time=datetime.time(18, 0)
        )


class TestBusinessMinutesBetween:
    def test_same_day_within_hours(self, business_hours):
        minutes = business_minutes_between(dt(MONDAY, 9), dt(MONDAY, 11))
        assert minutes == 120

    def test_full_business_day(self, business_hours):
        minutes = business_minutes_between(dt(MONDAY, 8), dt(MONDAY, 18))
        assert minutes == 600

    def test_clips_to_business_window(self, business_hours):
        minutes = business_minutes_between(dt(MONDAY, 6), dt(MONDAY, 20))
        assert minutes == 600

    def test_skips_weekend(self, business_hours):
        minutes = business_minutes_between(dt(FRIDAY, 17), dt(NEXT_MONDAY, 9))
        assert minutes == 120  # 1h sexta (17-18) + 1h segunda (08-09)

    def test_skips_holiday(self, business_hours):
        Holiday.objects.create(date=TUESDAY, name="Feriado de teste")
        minutes = business_minutes_between(dt(MONDAY, 17), dt(WEDNESDAY, 9))
        assert minutes == 120  # 1h segunda (17-18) + 1h quarta (08-09), terça pulada

    def test_zero_when_start_after_end(self, business_hours):
        assert business_minutes_between(dt(MONDAY, 11), dt(MONDAY, 9)) == 0


class TestAddBusinessMinutes:
    def test_same_day(self, business_hours):
        result = add_business_minutes(dt(MONDAY, 9), 60)
        assert result == dt(MONDAY, 10)

    def test_exactly_fills_the_day(self, business_hours):
        result = add_business_minutes(dt(MONDAY, 8), 600)
        assert result == dt(MONDAY, 18)

    def test_rolls_over_to_next_business_day(self, business_hours):
        result = add_business_minutes(dt(MONDAY, 17), 120)
        assert result == dt(TUESDAY, 9)

    def test_spec_example_friday_afternoon_crosses_weekend(self, business_hours):
        # Chamado aberto sexta às 17h com 4h de prazo vence segunda às 11h.
        result = add_business_minutes(dt(FRIDAY, 17), 240)
        assert result == dt(NEXT_MONDAY, 11)


@pytest.mark.django_db
class TestSLAState:
    @pytest.fixture(autouse=True)
    def _setup(self, business_hours):
        self.policy = SLAPolicy.objects.create(
            priority=Priority.ALTA, first_response_minutes=60, resolution_minutes=240
        )

    def test_green_when_under_yellow_threshold(self):
        ticket = TicketFactory(priority=Priority.ALTA)
        _set_created_at(ticket, dt(MONDAY, 9))
        ticket.first_response_at = dt(MONDAY, 9, 30)  # 30/60 = 50%
        ticket.save()

        status = first_response_sla(ticket, self.policy)

        assert status.state == SLAState.GREEN
        assert status.percent_consumed == pytest.approx(50)

    def test_yellow_at_75_percent(self):
        ticket = TicketFactory(priority=Priority.ALTA)
        _set_created_at(ticket, dt(MONDAY, 9))
        ticket.first_response_at = dt(MONDAY, 9, 45)  # 45/60 = 75%
        ticket.save()

        status = first_response_sla(ticket, self.policy)

        assert status.state == SLAState.YELLOW
        assert status.percent_consumed == pytest.approx(75)

    def test_red_when_overdue(self):
        ticket = TicketFactory(priority=Priority.ALTA)
        _set_created_at(ticket, dt(MONDAY, 9))
        ticket.first_response_at = dt(MONDAY, 10, 30)  # 90min > 60min alvo
        ticket.save()

        status = first_response_sla(ticket, self.policy)

        assert status.state == SLAState.RED
        assert status.percent_consumed > 100

    def test_deadline_matches_add_business_minutes(self):
        ticket = TicketFactory(priority=Priority.ALTA)
        _set_created_at(ticket, dt(MONDAY, 9))
        ticket.first_response_at = dt(MONDAY, 9, 30)
        ticket.save()

        status = first_response_sla(ticket, self.policy)

        assert status.deadline == dt(MONDAY, 10)  # 09:00 + 60min úteis


@pytest.mark.django_db
class TestSLAPause:
    @pytest.fixture(autouse=True)
    def _setup(self, business_hours):
        self.policy = SLAPolicy.objects.create(
            priority=Priority.ALTA, first_response_minutes=999999, resolution_minutes=240
        )

    def test_paused_time_is_excluded_from_elapsed(self):
        ticket = TicketFactory(priority=Priority.ALTA, status=Status.ABERTO)
        _set_created_at(ticket, dt(MONDAY, 9))

        _add_status_event(ticket, Status.EM_ANDAMENTO, dt(MONDAY, 9))
        _add_status_event(ticket, Status.AGUARDANDO_RESPOSTA, dt(MONDAY, 10))  # pausa às 10h
        _add_status_event(ticket, Status.EM_ANDAMENTO, dt(MONDAY, 14))  # retoma às 14h
        ticket.resolved_at = dt(MONDAY, 15)
        ticket.save()

        status = resolution_sla(ticket, self.policy)

        # Corrido: 09h-15h = 6h. Pausado: 10h-14h = 4h. Ativo: 2h = 120min.
        assert status.elapsed_minutes == pytest.approx(120)

    def test_deadline_shifts_forward_by_paused_duration(self):
        ticket = TicketFactory(priority=Priority.ALTA, status=Status.ABERTO)
        _set_created_at(ticket, dt(MONDAY, 9))

        _add_status_event(ticket, Status.EM_ANDAMENTO, dt(MONDAY, 9))
        _add_status_event(ticket, Status.AGUARDANDO_RESPOSTA, dt(MONDAY, 10))
        _add_status_event(ticket, Status.EM_ANDAMENTO, dt(MONDAY, 14))
        ticket.resolved_at = dt(MONDAY, 15)
        ticket.save()

        status = resolution_sla(ticket, self.policy)

        # Sem pausa o prazo venceria 09h+240min=13h; com 4h pausadas, 17h.
        assert status.deadline == dt(MONDAY, 17)

    def test_is_paused_reflects_current_status(self):
        ticket = TicketFactory(priority=Priority.ALTA, status=Status.ABERTO)
        _set_created_at(ticket, dt(MONDAY, 9))
        _add_status_event(ticket, Status.AGUARDANDO_RESPOSTA, dt(MONDAY, 10))

        status = resolution_sla(ticket, self.policy)

        assert status.is_paused is True
