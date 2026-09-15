import pytest
from django.db import IntegrityError, transaction

from accounts.factories import AdminFactory, AgentFactory, UserFactory
from accounts.models import User


@pytest.mark.django_db
class TestUserRoles:
    def test_user_role_helpers(self):
        user = UserFactory(role=User.Role.USER)
        assert user.is_user_role
        assert not user.is_agent
        assert not user.is_admin_role

    def test_agent_role_helpers_and_support_level(self):
        agent = AgentFactory(support_level=User.SupportLevel.N1)
        assert agent.is_agent
        assert agent.is_n1
        assert not agent.is_n2

    def test_admin_role_helper(self):
        admin = AdminFactory()
        assert admin.is_admin_role

    def test_email_must_be_unique(self):
        UserFactory(email="duplicado@example.com")
        with pytest.raises(IntegrityError), transaction.atomic():
            UserFactory(email="duplicado@example.com")
