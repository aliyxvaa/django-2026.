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


def test_ticket_admin_has_three_actions():
    site = AdminSite()
    model_admin = TicketAdmin(Ticket, site)

    assert "close_selected_tickets" in model_admin.actions
    assert "reopen_selected_tickets" in model_admin.actions
    assert "export_tickets_csv" in model_admin.actions
