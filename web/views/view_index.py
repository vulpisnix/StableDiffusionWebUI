from django.shortcuts import render
from django.urls import path
from django.views import View
from web.models import SDImage

class ViewIndex(View):
    template_name = 'landingpage.html'

    def get(self, request):
        return render(request, self.template_name, context={
            'images': SDImage.objects.all().reverse()
        })


urlpatterns = [
    path('', ViewIndex.as_view(), name='index'),
]