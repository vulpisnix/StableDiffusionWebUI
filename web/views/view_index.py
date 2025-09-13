from django.http import HttpResponse, FileResponse
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

class SDImageDownload(View):

    def get(self, request, *args, **kwargs):
        image_id = kwargs.get('image')
        found = SDImage.objects.filter(id=image_id)
        if found.exists():
            found = found.first()

            file_handle = found.image.open()
            response = FileResponse(file_handle, content_type='image/png')
            response['Content-Length'] = found.image.size
            response['Content-Disposition'] = 'attachment; filename="%s"' % found.image.name
    
            return response

        return HttpResponse(status=404, content="Requested Image not Found")


urlpatterns = [
    path('', ViewIndex.as_view(), name='index'),
    path('download/<int:image>/', SDImageDownload.as_view(), name='download_single'),
]