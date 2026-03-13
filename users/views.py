from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q


from ticketing.models import Ticket
from .models import Business, BusinessUser, Project


# ----------------------------------
# REGISTER (EXTERNAL USERS ONLY)
# ----------------------------------
def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        business_name = request.POST.get('business')
        project_id = request.POST.get('project')
        password = request.POST.get('password')

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered")
            return redirect('users:register')

        user = User.objects.create_user(
            username=email,     # username-based login
            email=email,
            password=password,
            first_name=name
        )

        project = Project.objects.get(id=project_id)

        business = Business.objects.create(
            name=business_name,
            email=email,
            phone=phone,
            project=project
        )

        BusinessUser.objects.create(
            user=user,
            user_type='EXTERNAL',
            business=business,
            project=project,
            role='CUSTOMER',
            designation='Customer'
        )

        login(request, user)
        return redirect('users:dashboard')

    projects = Project.objects.all()
    return render(request, 'users/register.html', {'projects': projects})


# ----------------------------------
# LOGIN (USERNAME BASED)
# ----------------------------------
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # email acts as username
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'users/login.html')


# ----------------------------------
# DASHBOARD (ROLE BASED)
# ----------------------------------
@login_required(login_url='users:login')
def dashboard(request):
    bu = BusinessUser.objects.get(user=request.user)

    # ========================
    # BASE QUERY (ROLE BASED)
    # ========================
    if bu.user_type == 'EXTERNAL':
        tickets = Ticket.objects.filter(raised_by=bu)

    else:
        if bu.role == 'DEPARTMENT':
            tickets = Ticket.objects.filter(
                project=bu.project,
                department=bu.department
            )

        elif bu.role == 'MANAGER':
            tickets = Ticket.objects.filter(project=bu.project)

        elif bu.role in ['CRM', 'ADMIN']:
            tickets = Ticket.objects.all()

        else:
            tickets = Ticket.objects.filter(assigned_to=bu)

    # ========================
    # SEARCH
    # ========================
    search = request.GET.get('search')
    if search:
        tickets = tickets.filter(
            Q(ticket_id__icontains=search) |
            Q(title__icontains=search) |
            Q(raised_by_name__icontains=search) |
            Q(shop_no__icontains=search)
        )

    # ========================
    # FILTERS
    # ========================
    department = request.GET.get('department')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # ⚠️ Project filter ONLY for internal users
    if bu.user_type != 'EXTERNAL':
        project = request.GET.get('project')
        if project:
            tickets = tickets.filter(project_id=project)

    if department:
        tickets = tickets.filter(department_id=department)

    if status:
        tickets = tickets.filter(status=status)

    if priority:
        tickets = tickets.filter(priority=priority)

    if date_from:
        tickets = tickets.filter(created_at__date__gte=date_from)

    if date_to:
        tickets = tickets.filter(created_at__date__lte=date_to)

    tickets = tickets.order_by('-created_at')

    # ========================
    # KPI COUNTS (FROM FILTERED DATA ✅)
    # ========================
    total_count = tickets.count()
    open_count = tickets.filter(status='OPEN').count()
    wip_count = tickets.filter(status='WIP').count()
    resolved_count = tickets.filter(status='RESOLVED').count()
    closed_count = tickets.filter(status='CLOSED').count()

    # ========================
    # SLA REMAINING
    # ========================
    for ticket in tickets:
        ticket.sla_remaining = (
            ticket.sla_deadline - timezone.now()
            if ticket.sla_deadline else None
        )

    return render(
        request,
        'users/dashboard.html',
        {
            'tickets': tickets,
            'role': bu.role,
            'user_type': bu.user_type,

            # KPI
            'total_count': total_count,
            'open_count': open_count,
            'wip_count': wip_count,
            'resolved_count': resolved_count,
            'closed_count': closed_count,

            # FILTER OPTIONS (FIXED)
            'projects': Project.objects.all(),
            'departments': BusinessUser.objects
                .filter(user_type='INTERNAL')
                .values('department__id', 'department__name')
                .distinct(),

            'statuses': Ticket.STATUS_CHOICES,
            'priorities': Ticket.PRIORITY_CHOICES,
        }
    )




# ----------------------------------
# LOGOUT
# ----------------------------------
@login_required
def user_logout(request):
    logout(request)
    return redirect('users:login')
