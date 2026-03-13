from django.urls import path
from . import views

app_name = "ticketing"

urlpatterns = [

    # --------------------
    # Ticket CRUD
    # --------------------
    path("create/", views.create_ticket, name="create_ticket"),

    path("<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),

    path("<int:ticket_id>/edit/", views.ticket_edit, name="ticket_edit"),

    path("<int:ticket_id>/delete/", views.ticket_delete, name="ticket_delete"),

    # --------------------
    # Department Staff Actions
    # --------------------
    path(
        "<int:ticket_id>/acknowledge/",
        views.ticket_acknowledge,
        name="ticket_acknowledge"
    ),

    path(
        "<int:ticket_id>/request-reassign/",
        views.ticket_request_reassign,
        name="ticket_request_reassign"
    ),

    path(
        "<int:ticket_id>/update-status/",
        views.ticket_update_status,
        name="ticket_update_status"
    ),

    # --------------------
    # Manager Actions
    # --------------------
    path(
        "<int:ticket_id>/reassign/",
        views.ticket_reassign,
        name="ticket_reassign"
    ),

    path(
        "<int:ticket_id>/reject-reassign/",
        views.ticket_reject_reassign,
        name="ticket_reject_reassign"
    ),
]
