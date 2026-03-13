from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages

from .forms import TicketForm
from .models import Ticket, TicketHistory
from users.models import BusinessUser


# =====================================================
# CREATE TICKET (CUSTOMER)
# =====================================================
@login_required
def create_ticket(request):
    bu = BusinessUser.objects.get(user=request.user)

    if bu.user_type != 'EXTERNAL':
        return redirect('users:dashboard')

    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.raised_by = bu
            ticket.raised_by_name = form.cleaned_data.get("raised_by_name") 
            ticket.business = bu.business
            ticket.project = bu.project

            ticket.assigned_to = BusinessUser.objects.filter(
                user_type='INTERNAL',
                project=ticket.project,
                department=ticket.department
            ).first()

            if ticket.priority == 'HIGH':
                ticket.sla_deadline = timezone.now() + timedelta(hours=4)
            elif ticket.priority == 'MEDIUM':
                ticket.sla_deadline = timezone.now() + timedelta(hours=24)
            else:
                ticket.sla_deadline = timezone.now() + timedelta(hours=72)

            ticket.save()

            TicketHistory.objects.create(
                ticket=ticket,
                action="Ticket Created",
                performed_by=bu,
                comment="Ticket raised by customer"
            )

            return redirect('users:dashboard')
    else:
        form = TicketForm()

    return render(request, 'ticketing/create_ticket.html', {'form': form})


# =====================================================
# TICKET DETAILS + TIMELINE
# =====================================================
@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    bu = BusinessUser.objects.get(user=request.user)

    if bu.role == 'CUSTOMER' and ticket.business != bu.business:
        return redirect('users:dashboard')

    if bu.role != 'CUSTOMER' and ticket.project != bu.project:
        return redirect('users:dashboard')

    timeline = ticket.history.all()  # ✅ FIX

    return render(
        request,
        'ticketing/ticket_detail.html',
        {
            'ticket': ticket,
            'timeline': timeline
        }
    )



# =====================================================
# EDIT TICKET (CUSTOMER)
# =====================================================
@login_required
def ticket_edit(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    bu = BusinessUser.objects.get(user=request.user)

    if bu.role != 'CUSTOMER' or ticket.status != 'OPEN':
        return redirect('users:dashboard')

    if request.method == 'POST':
        ticket.title = request.POST.get('title')
        ticket.description = request.POST.get('description')
        ticket.save()

        TicketHistory.objects.create(
            ticket=ticket,
            action="Ticket Edited",
            performed_by=bu,
            comment="Customer updated ticket details"
        )

        return redirect('users:dashboard')

    return render(request, 'ticketing/ticket_edit.html', {'ticket': ticket})


# =====================================================
# DELETE TICKET (CUSTOMER)
# =====================================================
@login_required
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    bu = BusinessUser.objects.get(user=request.user)

    if bu.role != 'CUSTOMER' or ticket.status != 'OPEN':
        return redirect('users:dashboard')

    if request.method == 'POST':
        TicketHistory.objects.create(
            ticket=ticket,
            action="Ticket Deleted",
            performed_by=bu,
            comment="Ticket deleted by customer"
        )
        ticket.delete()
        return redirect('users:dashboard')

    return render(request, 'ticketing/ticket_delete.html', {'ticket': ticket})


# =====================================================
# ACKNOWLEDGE TICKET (STAFF)
# =====================================================
@login_required
def ticket_acknowledge(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    bu = BusinessUser.objects.get(user=request.user)

    # ✅ Allowed roles
    if bu.role not in ['DEPARTMENT', 'MANAGER']:
        return redirect('users:dashboard')

    if ticket.status != 'OPEN':
        messages.warning(request, "Ticket already processed.")
        return redirect('users:dashboard')

    # ✅ Department ownership check ONLY for staff
    if bu.role == 'DEPARTMENT':
        if ticket.department != bu.department or ticket.project != bu.project:
            return redirect('users:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        # ===============================
        # 🔄 REQUEST REASSIGN (STAFF ONLY)
        # ===============================
        if action == 'reassign':
            if bu.role != 'DEPARTMENT':
                messages.error(request, "Only staff can request reassignment.")
                return redirect('users:dashboard')

            ticket.reassignment_requested = True
            ticket.reassignment_reason = request.POST.get('comment')
            ticket.save()

            TicketHistory.objects.create(
                ticket=ticket,
                action="Reassignment Requested",
                performed_by=bu,
                comment=request.POST.get('comment')
            )

            messages.success(request, "Reassignment request sent to manager.")
            return redirect('users:dashboard')

        # ===============================
        # ✅ ACKNOWLEDGE (STAFF + MANAGER)
        # ===============================
        hours = int(request.POST.get('tat_hours', 0))
        minutes = int(request.POST.get('tat_minutes', 0))

        ticket.tentative_tat = timedelta(hours=hours, minutes=minutes)
        ticket.status = 'WIP'
        ticket.acknowledged_at = timezone.now()
        ticket.acknowledged_by = bu

        # 🔐 Ownership transfer
        ticket.assigned_to = bu

        ticket.save()

        TicketHistory.objects.create(
            ticket=ticket,
            action="Ticket Acknowledged",
            old_status="OPEN",
            new_status="WIP",
            performed_by=bu,
            comment=request.POST.get('comment')
        )

        messages.success(request, "Ticket acknowledged and work started.")
        return redirect('users:dashboard')

    return render(request, 'ticketing/ticket_acknowledge.html', {'ticket': ticket})



# =====================================================
# UNLIMITED STATUS UPDATE (STAFF + MANAGER)
# =====================================================
@login_required
def ticket_update_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    bu = BusinessUser.objects.get(user=request.user)

    # Only internal users
    if bu.user_type != 'INTERNAL':
        return redirect('users:dashboard')

    # Staff can update only their project/department tickets
    if bu.role == 'DEPARTMENT':
        if ticket.department != bu.department or ticket.project != bu.project:
            return redirect('users:dashboard')

        # Staff must acknowledge first
        if not ticket.acknowledged_at:
            messages.warning(request, "Please acknowledge the ticket first.")
            return redirect('users:dashboard')

    if request.method == 'POST':
        old_status = ticket.status
        new_status = request.POST.get('status')
        comment = request.POST.get('comment')

        if new_status in dict(Ticket.STATUS_CHOICES):
            ticket.status = new_status
            if new_status == 'CLOSED':
                ticket.closed_at = timezone.now()
            ticket.save()

            TicketHistory.objects.create(
                ticket=ticket,
                action="Status Updated",
                old_status=old_status,
                new_status=new_status,
                performed_by=bu,
                comment=comment
            )

        return redirect('users:dashboard')

    # ALWAYS return response on GET
    return render(
        request,
        'ticketing/ticket_update_status.html',
        {
            'ticket': ticket,
            'status_choices': Ticket.STATUS_CHOICES
        }
    )



# =====================================================
# STAFF REQUEST REASSIGN
# =====================================================
@login_required
def ticket_request_reassign(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    bu = BusinessUser.objects.get(user=request.user)

    if ticket.status != 'OPEN':
        return redirect('users:dashboard')

    if bu.role != 'DEPARTMENT':
        return redirect('users:dashboard')

    if ticket.department != bu.department or ticket.project != bu.project:
        return redirect('users:dashboard')

    if request.method == 'POST':
        ticket.reassignment_requested = True
        ticket.reassignment_reason = request.POST.get('comment')
        ticket.save()

        TicketHistory.objects.create(
            ticket=ticket,
            action="Reassignment Requested",
            performed_by=bu,
            comment=request.POST.get('comment')
        )

        messages.success(request, "Reassignment request sent to manager")
        return redirect('users:dashboard')

    return render(request, 'ticketing/ticket_request_reassign.html', {'ticket': ticket})




# =====================================================
# MANAGER APPROVE REASSIGN
# =====================================================
@login_required
def ticket_reassign(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    bu = BusinessUser.objects.get(user=request.user)

    if bu.role != 'MANAGER':
        return redirect('users:dashboard')

    if ticket.acknowledged_at:
        messages.error(request, "Ticket already acknowledged. Reassignment locked.")
        return redirect('users:dashboard')

    if request.method == 'POST':
        new_staff_id = request.POST.get('staff')
        ticket.assigned_to = BusinessUser.objects.get(id=new_staff_id)
        ticket.reassignment_requested = False
        ticket.reassignment_reason = ""
        ticket.save()

        TicketHistory.objects.create(
            ticket=ticket,
            action="Ticket Reassigned",
            performed_by=bu,
            comment="Manager reassigned the ticket"
        )

        messages.success(request, "Ticket reassigned successfully")
        return redirect('users:dashboard')

    staff_list = BusinessUser.objects.filter(
        role='DEPARTMENT',
        project=ticket.project
    )

    return render(request, 'ticketing/manager_reassign.html', {
        'ticket': ticket,
        'staff_list': staff_list
    })


# =====================================================
# MANAGER REJECT REASSIGN
# =====================================================
@login_required
def ticket_reject_reassign(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    bu = BusinessUser.objects.get(user=request.user)

    if bu.role != 'MANAGER':
        return redirect('users:dashboard')

    ticket.reassignment_requested = False
    ticket.save()

    TicketHistory.objects.create(
        ticket=ticket,
        action="Reassignment Rejected",
        performed_by=bu,
        comment="Manager rejected reassignment request"
    )

    messages.success(request, "Reassignment request rejected")
    return redirect('users:dashboard')
