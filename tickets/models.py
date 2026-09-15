from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField("nome", max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Priority(models.TextChoices):
    BAIXA = "BAIXA", "Baixa"
    MEDIA = "MEDIA", "Média"
    ALTA = "ALTA", "Alta"
    CRITICA = "CRITICA", "Crítica"


class SLAPolicy(models.Model):
    priority = models.CharField(
        "prioridade", max_length=10, choices=Priority.choices, unique=True
    )
    first_response_minutes = models.PositiveIntegerField(
        "prazo de 1ª resposta (minutos úteis)"
    )
    resolution_minutes = models.PositiveIntegerField("prazo de resolução (minutos úteis)")

    class Meta:
        verbose_name = "política de SLA"
        verbose_name_plural = "políticas de SLA"
        ordering = ["first_response_minutes"]

    def __str__(self):
        return f"{self.get_priority_display()} — {self.resolution_minutes}min"


class BusinessHours(models.Model):
    class Weekday(models.IntegerChoices):
        SEGUNDA = 0, "Segunda-feira"
        TERCA = 1, "Terça-feira"
        QUARTA = 2, "Quarta-feira"
        QUINTA = 3, "Quinta-feira"
        SEXTA = 4, "Sexta-feira"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    weekday = models.IntegerField("dia da semana", choices=Weekday.choices, unique=True)
    start_time = models.TimeField("início")
    end_time = models.TimeField("fim")

    class Meta:
        verbose_name = "horário comercial"
        verbose_name_plural = "horários comerciais"
        ordering = ["weekday"]

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time}–{self.end_time}"


class Holiday(models.Model):
    date = models.DateField("data", unique=True)
    name = models.CharField("nome", max_length=150)

    class Meta:
        verbose_name = "feriado"
        verbose_name_plural = "feriados"
        ordering = ["date"]

    def __str__(self):
        return f"{self.date:%d/%m/%Y} — {self.name}"


class Status(models.TextChoices):
    ABERTO = "ABERTO", "Aberto"
    EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
    AGUARDANDO_RESPOSTA = "AGUARDANDO_RESPOSTA", "Aguardando resposta"
    RESOLVIDO = "RESOLVIDO", "Resolvido"
    FECHADO = "FECHADO", "Fechado"
    REABERTO = "REABERTO", "Reaberto"


class SupportLevel(models.TextChoices):
    N1 = "N1", "N1"
    N2 = "N2", "N2"


class Ticket(models.Model):
    readable_id = models.CharField(max_length=12, unique=True, blank=True, editable=False)

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_abertos"
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tickets_atribuidos",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name="tickets", null=True, blank=True
    )

    title = models.CharField("título", max_length=200)
    description = models.TextField("descrição")

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ABERTO
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIA
    )
    support_level = models.CharField(
        max_length=2, choices=SupportLevel.choices, default=SupportLevel.N1
    )

    created_at = models.DateTimeField(auto_now_add=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "chamado"
        verbose_name_plural = "chamados"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.readable_id} — {self.title}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.readable_id:
            self.readable_id = f"HD-{self.pk:04d}"
            super().save(update_fields=["readable_id"])


class Macro(models.Model):
    title = models.CharField("título", max_length=150)
    body_template = models.TextField(
        "texto",
        help_text="Use {{usuario}}, {{chamado}} e {{agente}} como variáveis.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "macro"
        verbose_name_plural = "macros"
        ordering = ["title"]

    def __str__(self):
        return self.title
