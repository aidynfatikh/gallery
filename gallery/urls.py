from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    # Home page for gallery
    path('', TemplateView.as_view(template_name='gallery/gallery_api.html'), name='home'),
    
    # API routes for images and actions
    path('api/images/', views.image_list, name='image-list'),
    path('api/upload/', views.upload_image, name='upload-image'),
    path('api/delete/<int:image_id>/', views.delete_image, name='delete-image'),
    path('api/search-image/', views.search_by_image, name='search-image'),
    path('api/generate-image/', views.generate_image, name='generate-image'),
]
