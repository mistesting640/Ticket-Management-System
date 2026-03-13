from django.contrib.auth.models import User
from django.db import models


class Location(models.Model):
    location_name = models.CharField(max_length=100)
    code = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.location_name} ({self.code})"

class Project(models.Model):
    """
    Mall / Cinema / Residential / Project
    """
    project_name = models.CharField(max_length=200)
    project_code = models.CharField(max_length=5)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    helpline_number = models.CharField(
        max_length=20,
        help_text="WhatsApp helpline number for ticket notifications",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.project_name} ({self.location.code})"


class Business(models.Model):
    """
    CUSTOMER ENTITY
    Shop / Resident / Visitor
    """
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class BusinessUser(models.Model):
    """
    ALL USERS IN SYSTEM
    """

    USER_TYPE_CHOICES = [
        ('INTERNAL', 'Internal User'),
        ('EXTERNAL', 'Customer User'),
    ]

    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('DEPARTMENT', 'Department User'),
        ('MANAGER', 'Project Manager'),
        ('CRM', 'CRM Head'),
        ('ADMIN', 'System Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10,choices=USER_TYPE_CHOICES,default='EXTERNAL')
    business = models.ForeignKey(Business,null=True,blank=True,on_delete=models.SET_NULL)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=20,choices=ROLE_CHOICES,default='CUSTOMER')
    designation = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    department = models.ForeignKey('ticketing.Department',null=True,blank=True,on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.user} ({self.role})"
    


