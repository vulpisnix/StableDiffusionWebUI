from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('c0re/', admin.site.urls),
    path('', include('web.urls')),
]
