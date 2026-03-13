from django.db import models
from django.utils import timezone
from users.models import Business, BusinessUser, Project
from django.conf import settings



class TicketType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.name} ({self.code})"



class SubCategory(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.department.name} - {self.name}"


class Ticket(models.Model):

    TICKET_TYPE_CHOICES = [
        ('INCIDENT REPORT', 'Incident Report'),
        ('SERVICE REQUEST', 'Service Request'),
        ('COMPLAINT', 'Complaint'),
        
    ]

    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('ASSIGNED', 'Assigned'),
        ('WIP', 'WIP'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    
    ticket_id = models.CharField(max_length=30, unique= True, null= True, blank=True, editable=False)

    # WHO & WHERE
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    raised_by = models.ForeignKey(BusinessUser, on_delete=models.CASCADE)
    raised_by_name = models.CharField(max_length=150,help_text="Name of person who raised the ticket")
    shop_no = models.PositiveIntegerField(help_text="Shop number")

    # ASSIGNMENT & LIFECYCLE
    assigned_to = models.ForeignKey(
        BusinessUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets')

    # WHAT
    ticket_type = models.ForeignKey(TicketType, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    sla_deadline = models.DateTimeField(null=True, blank=True)
    

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id and self.project and self.department:

            location_code = self.project.location.code
            project_code = self.project.project_code
            dept_code = self.department.code

            last_ticket = Ticket.objects.filter(
                project=self.project,
                department=self.department
            ).exclude(ticket_id__isnull=True).order_by('-id').first()

            if last_ticket and last_ticket.ticket_id:
                last_number = int(last_ticket.ticket_id[-4:])
                new_number = last_number + 1
            else:
                new_number = 1

            self.ticket_id = f"{location_code}{project_code}{dept_code}{new_number:04d}"

        super().save(*args, **kwargs)

    # Ticket acknowledge and re-assign

    acknowledged_at = models.DateTimeField(null=True, blank=True)

    tentative_tat = models.DurationField(
        null=True,
        blank=True,
        help_text="Estimated resolution time"
    )

    staff_comment = models.TextField(blank=True)

    reassignment_requested = models.BooleanField(default=False)
    reassignment_reason = models.TextField(blank=True)

    acknowledged_by = models.ForeignKey(
        BusinessUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='acknowledged_tickets'
    )

    @property
    def tat_deadline(self):
        if self.acknowledged_at and self.tentative_tat:
            return self.acknowledged_at + self.tentative_tat
        return None

    @property
    def tat_remaining(self):
        if self.tat_deadline:
            return self.tat_deadline - timezone.now()
        return None
    

    
class TicketHistory(models.Model):
    ticket = models.ForeignKey(
        "Ticket",
        on_delete=models.CASCADE,
        related_name="history"
    )

    action = models.CharField(max_length=100)
    old_status = models.CharField(max_length=50, blank=True, null=True)
    new_status = models.CharField(max_length=50, blank=True, null=True)

    comment = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        BusinessUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.ticket.ticket_id} - {self.action}"

