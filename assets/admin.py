from django.contrib import admin

from assets.models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("tag", "type", "brand_model", "owner", "status", "warranty_until")
    list_filter = ("type", "status")
    search_fields = ("tag", "brand_model", "serial_number")
    autocomplete_fields = ("owner",)
