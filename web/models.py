import json

from PIL import Image
from django.contrib.auth.models import User
from django.db import models

class Settings(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=500)

    class Meta:
        verbose_name_plural = 'Settings'
        verbose_name = 'Settings'

    def __str__(self):
        return self.name

class SDModel(models.Model):
    id = models.AutoField(primary_key=True)
    display_name = models.CharField(max_length=30)
    hgf_name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['enabled', 'display_name']
        verbose_name_plural = 'Models'
        verbose_name = 'Model'

    def __str__(self):
        return f"{self.display_name}"

class SDImage(models.Model):
    id = models.AutoField(primary_key=True)
    model = models.ForeignKey(SDModel, on_delete=models.DO_NOTHING)
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(default='error.png', upload_to='sd_images/')

    def get_metadata(self):
        sd_data = {
            'model': self.model.hgf_name
        }
        imgg = Image.open(self.image.path)
        if 'SD_Data' in imgg.info:
            sd_data = json.loads(imgg.info['SD_Data'])
            if 'settings' in sd_data:
                sd_data = sd_data['settings']

        model = self.model.hgf_name
        if 'model' not in sd_data and 'upscaler' in sd_data:
            model = sd_data['upscaler'] + " (Upscaler)"

        if 'model' in sd_data:
            model = sd_data['model'].split('/')[-1]

        return {
            'width': imgg.size[0],
            'height': imgg.size[1],
            'model': model,
        }

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Images'
        verbose_name = 'Image'

    def __str__(self):
        return f"Model: {self.model.display_name} | Creator: {self.creator.username}"