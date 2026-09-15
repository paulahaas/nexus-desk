import pytest
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.views import View

from accounts.factories import AgentFactory, UserFactory
from accounts.models import User
from accounts.permissions import RoleRequiredMixin, role_required


class _AgentOnlyView(RoleRequiredMixin, View):
    allowed_roles = (User.Role.AGENT, User.Role.ADMIN)

    def get(self, request):
        return HttpResponse("ok")


@role_required(User.Role.AGENT, User.Role.ADMIN)
def _agent_only_function_view(request):
    return HttpResponse("ok")


@pytest.mark.django_db
class TestRoleRequiredMixin:
    def test_allowed_role_can_access(self, rf: RequestFactory):
        request = rf.get("/fake")
        request.user = AgentFactory()

        response = _AgentOnlyView.as_view()(request)

        assert response.status_code == 200

    def test_disallowed_role_gets_permission_denied(self, rf: RequestFactory):
        request = rf.get("/fake")
        request.user = UserFactory(role=User.Role.USER)

        with pytest.raises(PermissionDenied):
            _AgentOnlyView.as_view()(request)


@pytest.mark.django_db
class TestRoleRequiredDecorator:
    def test_allowed_role_can_access(self, rf: RequestFactory):
        request = rf.get("/fake")
        request.user = AgentFactory()

        response = _agent_only_function_view(request)

        assert response.status_code == 200

    def test_disallowed_role_gets_permission_denied(self, rf: RequestFactory):
        request = rf.get("/fake")
        request.user = UserFactory(role=User.Role.USER)

        with pytest.raises(PermissionDenied):
            _agent_only_function_view(request)
