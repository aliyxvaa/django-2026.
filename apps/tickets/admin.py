import csv
from datetime import datetime, timedelta

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone

from .models import Category, Ticket


class OverdueFilter(admin.SimpleListFilter):
    title = "Просроченные"
    parameter_name = "overdue"

    def lookups(self, request, model_admin):
        return (("yes", "Да"), ("no", "Нет"))

    def queryset(self, request, queryset):
        cutoff = timezone.now() - timedelta(days=3)
        if self.value() == "yes":
            return queryset.filter(created_at__lt=cutoff).exclude(
                status="closed"
            )
        if self.value() == "no":
            return queryset.filter(created_at__gte=cutoff)
        return queryset


@admin.action(description="Закрыть выбранные заявки")
def close_tickets(modeladmin, request, queryset):
    updated = queryset.exclude(status="closed").update(status="closed")
    modeladmin.message_user(request, "Закрыто заявок: %s" % updated)


@admin.action(description="Повысить приоритет")
def raise_priority(modeladmin, request, queryset):
    updated = queryset.update(priority="high")
    modeladmin.message_user(request, "Приоритет повышен у %s заявок." % updated)


@admin.action(description="Экспорт в CSV")
def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = "tickets_%s.csv" % stamp
    response["Content-Disposition"] = "attachment; filename=%s" % filename
    response.write("\ufeff")

    writer = csv.writer(response)
    headers = ["ID", "Тема", "Категория", "Статус", "Автор", "Создано"]
    writer.writerow(headers)

    for ticket in queryset.select_related("author", "category"):
        category_name = ticket.category.name if ticket.category else "-"
        writer.writerow(
            [
                ticket.pk,
                ticket.title,
                category_name,
                ticket.get_status_display(),
                str(ticket.author),
                ticket.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )
    return response


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "status",
        "author",
        "created_at",
        "is_overdue_display",
    )
    list_filter = ("status", "category", "created_at", OverdueFilter)
    search_fields = ("title", "description", "author__username")
    autocomplete_fields = ("category",)
    date_hierarchy = "created_at"
    actions = [close_tickets, raise_priority, export_to_csv]

    @admin.display(boolean=True, description="Просрочена?")
    def is_overdue_display(self, obj):
        if obj.status == "closed":
            return False
        cutoff = timezone.now() - timedelta(days=3)
        return obj.created_at < cutoff

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(author=request.user)
