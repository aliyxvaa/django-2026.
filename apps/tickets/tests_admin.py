import pytest


from django.contrib.admin.sites import AdminSite


from apps.tickets.admin import TicketAdmin
from apps.tickets.models import Ticket
@pytest.mark.django_db
def test_ticket_priority_default(employee, category):
    ticket = Ticket.objects.create(
        title="Тестовая заявка",
        description="Проверка приоритета",
        category=category,
        author=employee,
    )
    assert ticket.priority == Ticket.Priority.NORMAL


@pytest.mark.django_db
def test_ticket_can_be_created_with_high_priority(employee, category):
    ticket = Ticket.objects.create(
        title="Срочная заявка",
        description="Нужна срочная помощь",
        category=category,
        author=employee,
        priority=Ticket.Priority.HIGH,
    )
    assert ticket.priority == Ticket.Priority.HIGH
def test_ticket_admin_has_required_columns():
    model_admin = TicketAdmin(Ticket, AdminSite())
    assert "priority" in model_admin.list_display
    assert "status" in model_admin.list_filter
    assert "priority" in model_admin.list_filter
    assert "created_at" in model_admin.list_filter
    assert "title" in model_admin.search_fields
    assert "description" in model_admin.search_fields
def test_ticket_admin_has_three_actions():
    model_admin = TicketAdmin(Ticket, AdminSite())
    assert "close_selected_tickets" in model_admin.actions
    assert "reopen_selected_tickets" in model_admin.actions
    assert "export_tickets_csv" in model_admin.actions



