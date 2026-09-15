from django.contrib import admin

from tickets.models import BusinessHours, Category, Holiday, Macro, SLAPolicy, Ticket, TicketEvent


class TicketEventInline(admin.TabularInline):
    model = TicketEvent
    extra = 0
    can_delete = False
    readonly_fields = ("author", "field", "from_value", "to_value", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ("priority", "first_response_minutes", "resolution_minutes")


@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ("weekday", "start_time", "end_time")


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("date", "name")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "readable_id",
        "title",
        "status",
        "priority",
        "support_level",
        "requester",
        "assignee",
        "created_at",
    )
    list_filter = ("status", "priority", "support_level", "category")
    search_fields = ("readable_id", "title", "description")
    autocomplete_fields = ("requester", "assignee", "category")
    inlines = [TicketEventInline]


@admin.register(Macro)
class MacroAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "created_at")
