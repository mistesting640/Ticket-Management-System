from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

def root_redirect(request):
    return redirect('/admin/')

urlpatterns = [
    path('', root_redirect),
    path('admin/', admin.site.urls),
<<<<<<< HEAD
]
=======
]
>>>>>>> 83d4c49657ff8fd5ec63bc676a1c63f1c51df31c
