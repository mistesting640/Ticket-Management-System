from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

def root_redirect(request):
    return redirect('/admin/')

urlpatterns = [
    path('', root_redirect),
    path('admin/', admin.site.urls),
]