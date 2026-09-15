from django.db import models
from django.utils.text import slugify

from tickets.models import Category


class Article(models.Model):
    title = models.CharField("título", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    content = models.TextField("conteúdo", help_text="Markdown")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name="articles", null=True, blank=True
    )
    views = models.PositiveIntegerField(default=0)
    helpful_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "artigo"
        verbose_name_plural = "artigos"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)
