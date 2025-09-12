import json
import os
from base64 import b64encode
from io import BytesIO

from PIL import Image
from django.shortcuts import render
from django.urls import path
from django.views import View

from SDWebUI import settings
from web.models import SDImage

class ViewIndex(View):
    template_name = 'landingpage.html'

    def get(self, request):
        return render(request, self.template_name, context={'images': SDImage.objects.all()})


urlpatterns = [
    path('', ViewIndex.as_view(), name='index'),
]