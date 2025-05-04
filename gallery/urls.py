from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    # Home page for gallery
    path('', TemplateView.as_view(template_name='gallery/gallery.html'), name='home'),
    
    # API routes for images and actions
    path('images/', views.list_images, name='list-images'),
    path('upload/', views.upload_image, name='upload-image'),
    path('delete/<int:image_id>/', views.delete_image, name='delete-image'),
    path('search-image/', views.search_by_image, name='search-image'),
    path('generate-image/', views.generate_image, name='generate-image'),
]
