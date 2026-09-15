import datetime

import pytest

from tickets.factories import CategoryFactory, MacroFactory, TicketFactory
from tickets.models import BusinessHours, Holiday, Priority, SLAPolicy


@pytest.mark.django_db
class TestTicketReadableId:
    def test_readable_id_is_generated_on_create(self):
        ticket = TicketFactory()

        assert ticket.readable_id.startswith("HD-")
        assert ticket.readable_id == f"HD-{ticket.pk:04d}"

    def test_readable_id_stays_stable_on_update(self):
        ticket = TicketFactory()
        original_id = ticket.readable_id

        ticket.title = "Título atualizado"
        ticket.save()

        ticket.refresh_from_db()
        assert ticket.readable_id == original_id

    def test_two_tickets_get_different_readable_ids(self):
        first = TicketFactory()
        second = TicketFactory()

        assert first.readable_id != second.readable_id


@pytest.mark.django_db
def test_category_str_is_name():
    category = CategoryFactory(name="Rede/VPN")
    assert str(category) == "Rede/VPN"


@pytest.mark.django_db
def test_sla_policy_unique_per_priority():
    SLAPolicy.objects.create(
        priority=Priority.ALTA, first_response_minutes=60, resolution_minutes=480
    )
    assert SLAPolicy.objects.filter(priority=Priority.ALTA).count() == 1


@pytest.mark.django_db
def test_business_hours_creation():
    bh = BusinessHours.objects.create(
        weekday=BusinessHours.Weekday.SEGUNDA,
        start_time=datetime.time(8, 0),
        end_time=datetime.time(18, 0),
    )
    assert "Segunda" in str(bh)


@pytest.mark.django_db
def test_holiday_creation():
    holiday = Holiday.objects.create(date=datetime.date(2026, 1, 1), name="Ano Novo")
    assert "Ano Novo" in str(holiday)


@pytest.mark.django_db
def test_macro_str_is_title():
    macro = MacroFactory(title="Senha redefinida")
    assert str(macro) == "Senha redefinida"
