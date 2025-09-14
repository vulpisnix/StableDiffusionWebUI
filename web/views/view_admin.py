from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import path
from django.views import View

from web.decorators import admin_required
from web.models import Settings, SDModel


class ViewIndex(View):
    template_name = 'dashboard/index.html'

    def get(self, request):
        return render(request, self.template_name, context={
            'models': SDModel.objects.all().reverse(),
        })

class ViewModelsDelete(View):
    def post(self, request, *args, **kwargs):
        modelId = kwargs.get('model')
        model = SDModel.objects.filter(id=modelId)
        if model.exists():
            model = model.first()
            model.delete()
            return JsonResponse({})
        return HttpResponse(status=404, content='not found')


class ViewUpdate_Settings(View):

    def get(self, request):
        settings = Settings.objects.all()
        payload = {}
        for setting in settings: payload[setting.name] = setting.value
        return JsonResponse(payload)

    def post(self, request):
        updated_fields = []
        for key in request.POST:
            value = request.POST[key]
            if Settings.objects.filter(name=key).exists():
                setting = Settings.objects.get(name=key)
                if setting.value != value:
                    setting.value = value
                    setting.save()
                    updated_fields.append(key)
        return JsonResponse({'message': 'Field updated.', 'fields': updated_fields})


urlpatterns = [
    path('', admin_required(ViewIndex.as_view()), name='admin_index'),
    path('models/delete/<int:model>/', admin_required(ViewModelsDelete.as_view()), name='admin_models_delete_api'),


    path('settings/', admin_required(ViewUpdate_Settings.as_view()), name='admin_settings_api'),
]