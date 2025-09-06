from django.shortcuts import render
from django.urls import path
from django.views import View


class ViewCreate(View):
    template_name = 'create.html'

    def get(self, request):
        return render(request, self.template_name, context={
            'models': [
                {
                    'id': 'stablediffusionapi/anything-v5',
                    'name': 'anything-v5'
                },
                {
                    'id': 'Qwen/Qwen-Image',
                    'name': 'Qwen-Image'
                }
            ]
        })


urlpatterns = [
    path('', ViewCreate.as_view(), name='create_index'),
]