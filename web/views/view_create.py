from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import path
from django.views import View

from web.models import SDModel


class ViewCreate(View):
    template_name = 'create.html'

    def get(self, request):
        return render(request, self.template_name, context={
            'models': SDModel.objects.filter(enabled=True).reverse(),
        })


urlpatterns = [
    path('', login_required(ViewCreate.as_view()), name='create_index'),
]