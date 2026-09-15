import pytest

from accounts.factories import AgentFactory
from tickets.factories import TicketFactory
from tickets.models import Priority, Status
from tickets.services import InvalidTransitionError, change_field, transition_status


@pytest.mark.django_db
class TestTransitionStatus:
    def test_valid_transition_updates_status(self):
        ticket = TicketFactory(status=Status.ABERTO)
        agent = AgentFactory()

        transition_status(ticket, Status.EM_ANDAMENTO, author=agent)

        ticket.refresh_from_db()
        assert ticket.status == Status.EM_ANDAMENTO

    def test_invalid_transition_raises(self):
        ticket = TicketFactory(status=Status.ABERTO)

        with pytest.raises(InvalidTransitionError):
            transition_status(ticket, Status.FECHADO)

    def test_fechado_is_terminal(self):
        ticket = TicketFactory(status=Status.RESOLVIDO)
        transition_status(ticket, Status.FECHADO)

        with pytest.raises(InvalidTransitionError):
            transition_status(ticket, Status.REABERTO)

    def test_transition_creates_ticket_event(self):
        ticket = TicketFactory(status=Status.ABERTO)
        agent = AgentFactory()

        transition_status(ticket, Status.EM_ANDAMENTO, author=agent)

        event = ticket.events.get(field="status")
        assert event.author == agent
        assert event.from_value == Status.ABERTO
        assert event.to_value == Status.EM_ANDAMENTO

    def test_leaving_aberto_sets_first_response_at(self):
        ticket = TicketFactory(status=Status.ABERTO)
        assert ticket.first_response_at is None

        transition_status(ticket, Status.EM_ANDAMENTO)

        ticket.refresh_from_db()
        assert ticket.first_response_at is not None

    def test_first_response_at_is_not_overwritten_on_later_transitions(self):
        ticket = TicketFactory(status=Status.ABERTO)
        transition_status(ticket, Status.EM_ANDAMENTO)
        ticket.refresh_from_db()
        first_response = ticket.first_response_at

        transition_status(ticket, Status.AGUARDANDO_RESPOSTA)
        ticket.refresh_from_db()

        assert ticket.first_response_at == first_response

    def test_resolvido_sets_resolved_at(self):
        ticket = TicketFactory(status=Status.EM_ANDAMENTO)

        transition_status(ticket, Status.RESOLVIDO)

        ticket.refresh_from_db()
        assert ticket.resolved_at is not None

    def test_reaberto_clears_resolved_at(self):
        ticket = TicketFactory(status=Status.RESOLVIDO)
        ticket.resolved_at = ticket.created_at
        ticket.save()

        transition_status(ticket, Status.REABERTO)

        ticket.refresh_from_db()
        assert ticket.resolved_at is None

    def test_fechado_sets_closed_at(self):
        ticket = TicketFactory(status=Status.RESOLVIDO)

        transition_status(ticket, Status.FECHADO)

        ticket.refresh_from_db()
        assert ticket.closed_at is not None


@pytest.mark.django_db
class TestChangeField:
    def test_change_field_updates_value_and_logs_event(self):
        ticket = TicketFactory(priority=Priority.BAIXA)
        agent = AgentFactory()

        change_field(ticket, "priority", Priority.CRITICA, author=agent)

        ticket.refresh_from_db()
        assert ticket.priority == Priority.CRITICA
        event = ticket.events.get(field="priority")
        assert event.from_value == Priority.BAIXA
        assert event.to_value == Priority.CRITICA
        assert event.author == agent

    def test_change_field_is_a_noop_when_value_is_unchanged(self):
        ticket = TicketFactory(priority=Priority.BAIXA)

        change_field(ticket, "priority", Priority.BAIXA)

        assert ticket.events.filter(field="priority").count() == 0

    def test_change_field_handles_assignee(self):
        ticket = TicketFactory(assignee=None)
        agent = AgentFactory()

        change_field(ticket, "assignee", agent)

        ticket.refresh_from_db()
        assert ticket.assignee == agent
        event = ticket.events.get(field="assignee")
        assert event.from_value == ""
        assert event.to_value == str(agent)
