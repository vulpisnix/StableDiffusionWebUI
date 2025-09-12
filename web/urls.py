from django.urls import path, include

urlpatterns = [
    path('', include('web.views.view_index')),
    path('', include('web.views.view_auth')),

    path('create/', include('web.views.view_create')),
    path('admin/', include('web.views.view_admin')),
]