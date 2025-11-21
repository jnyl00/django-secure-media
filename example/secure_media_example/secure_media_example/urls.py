"""
URL configuration for secure_media_example project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import path
from django.contrib.auth.decorators import login_required

from django_secure_media.decorators import secure_media_path

from .views import CatalogView, UploadFileView, DeleteFileView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', CatalogView.as_view(), name="catalog"),
    path('upload/', login_required(UploadFileView.as_view()), name="file_upload"),
    path('delete/<str:path_code>', login_required(DeleteFileView.as_view()), name="file_delete"),
]

urlpatterns += static(settings.MEDIA_URL, view=secure_media_path(serve), document_root=settings.MEDIA_ROOT)
