from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from SDWebUI import settings

urlpatterns = [
    path('c0re/', admin.site.urls),
    path('', include('web.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)