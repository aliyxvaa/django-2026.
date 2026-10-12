```python
from django.contrib import admin
from django.http import HttpRequest

from .models import Category, Ticket


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


class TicketInline(admin.TabularInline):
    model = Ticket
    fk_name = "author"
    fields = ("title", "category", "status", "priority", "created_at")
    readonly_fields = ("created_at",)
    extra = 0
    show_change_link = True


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "status",
        "priority",
        "author",
        "assignee",
        "created_at",
        "is_overdue",
    )

    list_filter = ("status", "priority", "created_at", "category")
    search_fields = (
        "title",
        "description",
        "author__username",
        "author__first_name",
        "author__last_name",
        "assignee__username",
    )
    autocomplete_fields = ("category", "author", "assignee")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("category", "author", "assignee")
    inlines = (TicketInline,)

    @admin.display(description="Критическая заявка", boolean=True)
    def is_overdue(self, obj):
        return obj.priority == Ticket.Priority.CRITICAL

    @admin.action(description="Закрыть выбранные заявки")
    def close_selected_tickets(self, request, queryset):
        updated = queryset.exclude(
            status__in=(Ticket.Status.DONE, Ticket.Status.REJECTED)
        ).update(status=Ticket.Status.DONE)
        self.message_user(request, f"Закрыто заявок: {updated}")

    @admin.action(description="Вернуть выбранные заявки в новые")
    def reopen_selected_tickets(self, request, queryset):
        updated = queryset.update(status=Ticket.Status.NEW)
        self.message_user(request, f"Возвращено в новые: {updated}")

    actions = ("close_selected_tickets", "reopen_selected_tickets")

    def get_queryset(self, request: HttpRequest):
        queryset = super().get_queryset(request)

        if request.user.is_superuser or request.user.is_staff and request.user.is_manager:
            return queryset

        if request.user.is_staff and request.user.is_agent:
            return queryset.filter(assignee=request.user)

        return queryset.filter(author=request.user)
```
