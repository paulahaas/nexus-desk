from django.contrib import admin

from knowledge.models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "views", "helpful_votes", "created_at")
    list_filter = ("category",)
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
