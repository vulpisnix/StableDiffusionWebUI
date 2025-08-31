from django.shortcuts import render
from django.urls import path
from django.views import View


class ViewIndex(View):
    template_name = 'landingpage.html'

    def get(self, request):
        return render(request, self.template_name)


urlpatterns = [
    path('', ViewIndex.as_view(), name='index'),
]