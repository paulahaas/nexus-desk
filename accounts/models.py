from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = "USER", "Usuário"
        AGENT = "AGENT", "Agente"
        ADMIN = "ADMIN", "Admin"

    class SupportLevel(models.TextChoices):
        N1 = "N1", "N1"
        N2 = "N2", "N2"

    email = models.EmailField("e-mail", unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    department = models.CharField("departamento", max_length=100, blank=True)
    support_level = models.CharField(
        "nível de suporte",
        max_length=2,
        choices=SupportLevel.choices,
        blank=True,
        help_text="Preenchido apenas para usuários com papel Agente.",
    )

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_user_role(self):
        return self.role == self.Role.USER

    @property
    def is_agent(self):
        return self.role == self.Role.AGENT

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_n1(self):
        return self.is_agent and self.support_level == self.SupportLevel.N1

    @property
    def is_n2(self):
        return self.is_agent and self.support_level == self.SupportLevel.N2
