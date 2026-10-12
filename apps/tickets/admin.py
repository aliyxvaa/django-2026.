import csv
from datetime import datetime, timedelta

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone

from .models import Category, Ticket


# ---------- Кастомный фильтр ----------
class OverdueFilter(admin.SimpleListFilter):
    title = "Просроченные"
    parameter_name = "overdue"

    def lookups(self, request, model_admin):
        return (("yes", "Да"), ("no", "Нет"))

    def queryset(self, request, queryset):
        cutoff = timezone.now() - timedelta(days=3)
        if self.value() == "yes":
            return queryset.filter(created_at__lt=cutoff).exclude(status="closed")
        if self.value() == "no":
            return queryset.filter(created_at__gte=cutoff)
        return queryset


# ---------- Действия ----------
@admin.action(description="Закрыть выбранные заявки")
def close_tickets(modeladmin, request, queryset):
    updated = queryset.exclude(status="closed").update(status="closed")
    modeladmin.message_user(request, f"Закрыто заявок: {updated}")


@admin.action(description="Повысить приоритет до HIGH")
def raise_priority(modeladmin, request, queryset):
    try:
        updated = queryset.update(priority="high")
        modeladmin.message_user(request, f"Приоритет повышен у {updated} заявок.")
    except Exception:
        modeladmin.message_user(request, "Поле priority не найдено в модели Ticket.", level=40)


@admin.action(description="Экспорт в CSV")
def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="tickets_{datetime.now():%Y%m%d_%H%M}.csv"'
    )
    response.write("\ufeff")  # BOM для Excel
    writer = csv.writer(response)
    writer.writerow(["ID", "Тема", "Категория", "Статус", "Автор", "Исполнитель", "Создано"])
    for t in queryset.select_related("author", "assignee", "category"):
        writer.writerow([
            t.pk,
            t.title,
            getattr(t.category, "name", "—") if t.category else "—",
            t.get_status_display() if hasattr(t, "get_status_display") else t.status,
            str(t.author),
            str(t.assignee) if t.assignee else "—",
            t.created_at.strftime("%Y-%m-%d %H:%M"),
        ])
    return response


# ---------- Category ----------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# ---------- Ticket ----------
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "category", "status",
        "author", "assignee", "created_at", "is_overdue_display",
    )
    list_filter = ("status", "category", "created_at", OverdueFilter)
    search_fields = ("title", "description", "author__username", "author__first_name")
    autocomplete_fields = ("category",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    actions = [close_tickets, raise_priority, export_to_csv]

    @admin.display(boolean=True, description="Просрочена?")
    def is_overdue_display(self, obj):
        if obj.status == "closed":
            return False
        return obj.created_at < timezone.now() - timedelta(days=3)

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="managers").exists():
            return qs
        return qs.filter(author=request.user)
