from django.conf import settings
from django.db import models


class AssetType(models.TextChoices):
    NOTEBOOK = "NOTEBOOK", "Notebook"
    DESKTOP = "DESKTOP", "Desktop"
    MONITOR = "MONITOR", "Monitor"
    PERIFERICO = "PERIFERICO", "Periférico"
    CELULAR = "CELULAR", "Celular"


class AssetStatus(models.TextChoices):
    EM_USO = "EM_USO", "Em uso"
    ESTOQUE = "ESTOQUE", "Estoque"
    MANUTENCAO = "MANUTENCAO", "Manutenção"
    DESCARTADO = "DESCARTADO", "Descartado"


class Asset(models.Model):
    tag = models.CharField("tag de patrimônio", max_length=30, unique=True)
    type = models.CharField("tipo", max_length=20, choices=AssetType.choices)
    brand_model = models.CharField("marca/modelo", max_length=150)
    serial_number = models.CharField("número de série", max_length=100, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assets",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20, choices=AssetStatus.choices, default=AssetStatus.ESTOQUE
    )
    purchased_at = models.DateField("data de compra", null=True, blank=True)
    warranty_until = models.DateField("fim da garantia", null=True, blank=True)

    class Meta:
        verbose_name = "ativo"
        verbose_name_plural = "ativos"
        ordering = ["tag"]

    def __str__(self):
        return f"{self.tag} — {self.brand_model}"
