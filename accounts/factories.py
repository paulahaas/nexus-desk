import factory

from accounts.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = "Test"
    last_name = "User"
    role = User.Role.USER
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class AgentFactory(UserFactory):
    role = User.Role.AGENT
    support_level = User.SupportLevel.N1


class AdminFactory(UserFactory):
    role = User.Role.ADMIN
    is_staff = True
