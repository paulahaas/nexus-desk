import factory

from accounts.factories import UserFactory
from tickets.models import Category, Macro, Priority, Status, SupportLevel, Ticket


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Categoria {n}")


class TicketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ticket

    requester = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    title = "Chamado de teste"
    description = "Descrição de teste."
    priority = Priority.MEDIA
    status = Status.ABERTO
    support_level = SupportLevel.N1


class MacroFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Macro

    title = factory.Sequence(lambda n: f"Macro {n}")
    body_template = "Olá {{usuario}}, sobre o chamado {{chamado}}..."
