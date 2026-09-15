import pytest
from django.core.management import call_command

from accounts.models import User
from assets.models import Asset
from knowledge.models import Article
from tickets.models import BusinessHours, Category, Holiday, Macro, SLAPolicy, Ticket


@pytest.mark.django_db
def test_seed_demo_creates_expected_data():
    call_command("seed_demo")

    assert User.objects.filter(role=User.Role.ADMIN).count() == 1
    assert User.objects.filter(role=User.Role.AGENT).count() == 4
    assert User.objects.filter(role=User.Role.AGENT, support_level="N1").count() == 2
    assert User.objects.filter(role=User.Role.AGENT, support_level="N2").count() == 2
    assert User.objects.filter(role=User.Role.USER).count() == 20

    assert Category.objects.count() == 6
    assert SLAPolicy.objects.count() == 4
    assert BusinessHours.objects.count() == 5
    assert Holiday.objects.count() == 8
    assert Macro.objects.count() == 15
    assert Article.objects.count() == 15
    assert Asset.objects.count() == 50
    assert Ticket.objects.count() == 250

    for ticket in Ticket.objects.filter(status="ABERTO"):
        assert ticket.assignee is None
        assert ticket.first_response_at is None

    for ticket in Ticket.objects.exclude(status="ABERTO"):
        assert ticket.assignee is not None
        assert ticket.first_response_at is not None


@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")

    assert Ticket.objects.count() == 250
    assert User.objects.filter(role=User.Role.USER).count() == 20
