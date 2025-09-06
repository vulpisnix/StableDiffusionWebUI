import json
import os
from base64 import b64encode
from io import BytesIO

from PIL import Image
from django.shortcuts import render
from django.urls import path
from django.views import View

from SDWebUI import settings


IMG_CACHE = []
IMAGES_CACHE = []

class ViewIndex(View):
    template_name = 'landingpage.html'

    def get(self, request):
        raw_images_pre = os.listdir(os.path.join(settings.MEDIA_ROOT, 'sd_images'))
        raw_images = []
        for r in raw_images_pre:
            if r not in IMG_CACHE and r.endswith('.png') and not r.startswith('_'):
                raw_images.append(r)

        images = IMAGES_CACHE
        for img in raw_images:
            IMG_CACHE.append(img)
            imgg = Image.open(os.path.join(settings.MEDIA_ROOT, 'sd_images', img))
            buffer = BytesIO()
            imgg.save(buffer, format="PNG")
            buffer.seek(0)

            sd_data = {
                'model': 'Unknown/Unknown'
            }

            if 'SD_Data' in imgg.info:
                sd_data = json.loads(imgg.info['SD_Data'])['settings']

            images.insert(0, {
                'width': imgg.size[0],
                'height': imgg.size[1],
                'base64': b64encode(buffer.getvalue()).decode(),
                'model': sd_data['model'].split('/')[-1],
            })

        return render(request, self.template_name, context={'images': images})


urlpatterns = [
    path('', ViewIndex.as_view(), name='index'),
]