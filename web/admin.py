from django.contrib import admin

from web.models import SDModel, SDImage, SDImageQueue

# Register your models here.
admin.site.register(SDModel)
admin.site.register(SDImage)
admin.site.register(SDImageQueue)