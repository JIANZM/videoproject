from django.contrib import admin

# Register your models here.
from .models import Video,Classification

admin.site.register(Video)
admin.site.register(Classification)