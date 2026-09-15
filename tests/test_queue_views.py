import pytest
from django.db import connection
from django.urls import reverse

from accounts.factories import AdminFactory, AgentFactory, UserFactory
from accounts.models import User
from tickets.factories import CategoryFactory, TicketFactory
from tickets.models import Priority, SLAPolicy, Status


@pytest.fixture(autouse=True)
def sla_policies(db):
    """_attach_sla roda pra todo chamado exibido na fila; sem política de
    SLA cadastrada pra prioridade do chamado, SLAPolicy.objects.get estoura."""
    for priority, first, resolution in [
        (Priority.BAIXA, 480, 2880),
        (Priority.MEDIA, 240, 1440),
        (Priority.ALTA, 60, 480),
        (Priority.CRITICA, 30, 240),
    ]:
        SLAPolicy.objects.create(
            priority=priority, first_response_minutes=first, resolution_minutes=resolution
        )


@pytest.mark.django_db
class TestQueueScope:
    def test_plain_user_only_sees_their_own_tickets(self, client):
        user = UserFactory(role=User.Role.USER)
        other = UserFactory(role=User.Role.USER)
        mine = TicketFactory(requester=user, title="Meu chamado")
        TicketFactory(requester=other, title="Chamado de outra pessoa")
        client.force_login(user)

        response = client.get(reverse("tickets:queue"))

        tickets = list(response.context["page_obj"])
        assert tickets == [mine]

    def test_agent_sees_every_ticket(self, client):
        agent = AgentFactory()
        TicketFactory(title="A")
        TicketFactory(title="B")
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"))

        assert response.context["page_obj"].paginator.count == 2

    def test_plain_user_cannot_see_management_filters(self, client):
        user = UserFactory(role=User.Role.USER)
        client.force_login(user)

        response = client.get(reverse("tickets:queue"))

        assert response.context["can_manage_queue"] is False
        assert "Sem responsável" not in response.content.decode()


@pytest.mark.django_db
class TestQueueFilters:
    def test_filter_by_status(self, client):
        agent = AgentFactory()
        open_ticket = TicketFactory(status=Status.ABERTO)
        TicketFactory(status=Status.EM_ANDAMENTO)
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"), {"status": Status.ABERTO})

        assert list(response.context["page_obj"]) == [open_ticket]

    def test_filter_by_priority(self, client):
        agent = AgentFactory()
        critical = TicketFactory(priority=Priority.CRITICA)
        TicketFactory(priority=Priority.BAIXA)
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"), {"priority": Priority.CRITICA})

        assert list(response.context["page_obj"]) == [critical]

    def test_filter_by_category(self, client):
        agent = AgentFactory()
        category = CategoryFactory(name="Rede/VPN")
        matching = TicketFactory(category=category)
        TicketFactory(category=CategoryFactory(name="Hardware"))
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"), {"category": category.pk})

        assert list(response.context["page_obj"]) == [matching]

    def test_mine_filter(self, client):
        agent = AgentFactory()
        other_agent = AgentFactory()
        mine = TicketFactory(assignee=agent)
        TicketFactory(assignee=other_agent)
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"), {"mine": "1"})

        assert list(response.context["page_obj"]) == [mine]

    def test_unassigned_filter(self, client):
        agent = AgentFactory()
        unassigned = TicketFactory(assignee=None)
        TicketFactory(assignee=agent)
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"), {"unassigned": "1"})

        assert list(response.context["page_obj"]) == [unassigned]

    def test_invalid_filter_values_are_ignored_not_erroring(self, client):
        agent = AgentFactory()
        TicketFactory()
        client.force_login(agent)

        response = client.get(
            reverse("tickets:queue"), {"status": "not-a-status", "category": "nope"}
        )

        assert response.status_code == 200

    @pytest.mark.skipif(
        connection.vendor != "postgresql", reason="SearchVector exige PostgreSQL"
    )
    def test_search_matches_title(self, client):
        agent = AgentFactory()
        target = TicketFactory(title="VPN cai toda hora", description="Rede instável")
        TicketFactory(title="Impressora sem toner", description="Sem papel também")
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"), {"q": "VPN"})

        assert list(response.context["page_obj"]) == [target]

    @pytest.mark.skipif(
        connection.vendor != "postgresql", reason="SearchVector exige PostgreSQL"
    )
    def test_search_matches_readable_id(self, client):
        agent = AgentFactory()
        target = TicketFactory()
        TicketFactory()
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"), {"q": target.readable_id})

        assert list(response.context["page_obj"]) == [target]


@pytest.mark.django_db
class TestQueueRiskFilter:
    def test_risk_filter_excludes_resolved_and_closed(self, client):
        agent = AgentFactory()
        TicketFactory(status=Status.RESOLVIDO)
        TicketFactory(status=Status.FECHADO)
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"), {"risk": "1"})

        assert response.context["page_obj"].paginator.count == 0


@pytest.mark.django_db
class TestQueuePagination:
    def test_paginates_at_page_size(self, client):
        agent = AgentFactory()
        for _ in range(30):
            TicketFactory()
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"))

        page_obj = response.context["page_obj"]
        assert len(page_obj.object_list) == 25
        assert page_obj.paginator.num_pages == 2

    def test_second_page(self, client):
        agent = AgentFactory()
        for _ in range(30):
            TicketFactory()
        client.force_login(agent)

        response = client.get(reverse("tickets:queue"), {"page": 2})

        assert len(response.context["page_obj"].object_list) == 5


@pytest.mark.django_db
class TestAssumeTicket:
    def test_agent_can_assume_unassigned_ticket(self, client):
        agent = AgentFactory()
        ticket = TicketFactory(assignee=None)
        client.force_login(agent)

        response = client.post(reverse("tickets:assume", args=[ticket.pk]))

        assert response.status_code == 204
        assert response.headers["HX-Trigger"] == "ticket-assumed"
        ticket.refresh_from_db()
        assert ticket.assignee == agent
        assert ticket.events.filter(field="assignee").exists()

    def test_plain_user_cannot_assume(self, client):
        user = UserFactory(role=User.Role.USER)
        ticket = TicketFactory(assignee=None)
        client.force_login(user)

        response = client.post(reverse("tickets:assume", args=[ticket.pk]))

        assert response.status_code == 403
        ticket.refresh_from_db()
        assert ticket.assignee is None

    def test_admin_can_assume(self, client):
        admin = AdminFactory()
        ticket = TicketFactory(assignee=None)
        client.force_login(admin)

        response = client.post(reverse("tickets:assume", args=[ticket.pk]))

        assert response.status_code == 204

    def test_get_is_not_allowed(self, client):
        agent = AgentFactory()
        ticket = TicketFactory(assignee=None)
        client.force_login(agent)

        response = client.get(reverse("tickets:assume", args=[ticket.pk]))

        assert response.status_code == 405
