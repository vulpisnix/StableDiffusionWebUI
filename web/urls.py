from django.urls import path, include

urlpatterns = [
    path('', include('web.views.view_index')),
    path('create/', include('web.views.view_create'))
]