```python
from django.contrib import admin
import csv
from django.http import HttpRequest, HttpResponse

from .models import Category, Ticket


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)

    @admin.action(description="Экспортировать выбранные заявки в CSV")
    def export_tickets_csv(self, request, queryset):
        response = HttpResponse(
            content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = (
            'attachment; filename="tickets.csv"'
        )
        response.write("\ufeff")

        writer = csv.writer(response)
        writer.writerow([
            "ID",
            "Тема",
            "Категория",
            "Статус",
            "Приоритет",
            "Автор",
            "Исполнитель",
            "Дата создания",
        ])

        for ticket in queryset.select_related(
            "category", "author", "assignee"
        ):
            writer.writerow([
                ticket.pk,
                ticket.title,
                ticket.category.name,
                ticket.get_status_display(),
                ticket.get_priority_display(),
                ticket.author,
                ticket.assignee or "",
                ticket.created_at,
            ])

        return response


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

    actions = (
    "close_selected_tickets",
    "reopen_selected_tickets",
    "export_tickets_csv",
)

    def get_queryset(self, request: HttpRequest):
        queryset = super().get_queryset(request)

        if request.user.is_superuser or request.user.is_staff and request.user.is_manager:
            return queryset

        if request.user.is_staff and request.user.is_agent:
            return queryset.filter(assignee=request.user)

        return queryset.filter(author=request.user)
```
