from django.contrib import admin
from .models import Project, Business, BusinessUser, Location

admin.site.register(Project)
admin.site.register(Business)
admin.site.register(BusinessUser)
admin.site.register(Location)