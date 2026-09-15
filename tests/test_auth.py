import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse

from accounts.factories import UserFactory


@pytest.mark.django_db
class TestLogin:
    def test_valid_credentials_log_in_and_redirect_home(self, client):
        user = UserFactory(username="maria")
        user.set_password("senha-forte-123")
        user.save()

        response = client.post(
            reverse("login"), {"username": "maria", "password": "senha-forte-123"}
        )

        assert response.status_code == 302
        assert response.url == reverse("home")

    def test_invalid_credentials_do_not_log_in(self, client):
        UserFactory(username="joao")

        response = client.post(
            reverse("login"), {"username": "joao", "password": "senha-errada"}
        )

        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

    def test_home_requires_login(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 302
        assert reverse("login") in response.url


@pytest.mark.django_db
def test_logout(client):
    user = UserFactory(username="carla")
    user.set_password("senha-forte-123")
    user.save()
    client.login(username="carla", password="senha-forte-123")

    response = client.post(reverse("logout"))

    assert response.status_code == 200  # renderiza logged_out.html direto
    home_response = client.get(reverse("home"))
    assert home_response.status_code == 302


@pytest.mark.django_db
def test_password_reset_sends_email(client):
    UserFactory(username="reset.me", email="reset.me@example.com")

    response = client.post(reverse("password_reset"), {"email": "reset.me@example.com"})

    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "reset.me@example.com" in mail.outbox[0].to


@pytest.mark.django_db
def test_password_reset_for_unknown_email_does_not_leak_existence(client):
    response = client.post(reverse("password_reset"), {"email": "ninguem@example.com"})

    assert response.status_code == 302
    assert len(mail.outbox) == 0


@pytest.mark.django_db
@override_settings(AXES_ENABLED=True, AXES_FAILURE_LIMIT=3)
def test_login_is_rate_limited_after_repeated_failures(client):
    UserFactory(username="alvo")

    for _ in range(3):
        client.post(reverse("login"), {"username": "alvo", "password": "errada"})

    response = client.post(reverse("login"), {"username": "alvo", "password": "errada"})

    assert response.status_code == 429


@pytest.mark.django_db
class TestDemoLogin:
    @override_settings(DEMO_MODE=True)
    def test_logs_in_as_the_fixed_demo_account_for_the_role(self, client):
        UserFactory(username="admin", role="ADMIN")

        response = client.post(reverse("demo_login", kwargs={"role": "admin"}))

        assert response.status_code == 302
        assert response.url == reverse("home")
        home = client.get(reverse("home"))
        assert home.wsgi_request.user.username == "admin"

    @override_settings(DEMO_MODE=True)
    def test_unknown_role_is_404(self, client):
        response = client.post(reverse("demo_login", kwargs={"role": "superhacker"}))
        assert response.status_code == 404

    @override_settings(DEMO_MODE=True)
    def test_get_is_not_allowed(self, client):
        UserFactory(username="admin", role="ADMIN")
        response = client.get(reverse("demo_login", kwargs={"role": "admin"}))
        assert response.status_code == 404

    @override_settings(DEMO_MODE=False)
    def test_disabled_when_demo_mode_is_off(self, client):
        UserFactory(username="admin", role="ADMIN")
        response = client.post(reverse("demo_login", kwargs={"role": "admin"}))
        assert response.status_code == 404
