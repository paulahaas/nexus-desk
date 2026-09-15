import pytest
from django.urls import reverse

from accounts.factories import AgentFactory, UserFactory
from accounts.models import User


@pytest.mark.django_db
class TestSidebarNav:
    def test_plain_user_does_not_see_agent_only_nav_items(self, client):
        user = UserFactory(role=User.Role.USER)
        client.force_login(user)

        response = client.get(reverse("home"))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Inventário" not in content
        assert "Métricas" not in content

    def test_agent_sees_inventory_but_not_metrics(self, client):
        agent = AgentFactory()
        client.force_login(agent)

        response = client.get(reverse("home"))

        content = response.content.decode()
        assert "Inventário" in content
        assert "Métricas" not in content

    def test_admin_sees_every_nav_item(self, client):
        admin = UserFactory(role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("home"))

        content = response.content.decode()
        assert "Inventário" in content
        assert "Métricas" in content
