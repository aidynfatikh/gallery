from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # Home page for gallery
    path('', TemplateView.as_view(template_name='gallery/gallery.html'), name='home'),
    
    # API routes for images and actions
    path('images/', views.list_images, name='list-images'),
    path('upload/', views.upload_image, name='upload-image'),
    path('delete/<int:image_id>/', views.delete_image, name='delete-image'),
    path('search-image/', views.search_by_image, name='search-image'),
    path('generate-image/', views.generate_image, name='generate-image'),
    path('like/<int:image_id>/', views.like_image, name='like_image'),
    path('unlike/<int:image_id>/', views.unlike_image, name='unlike_image'),
    path('post-data/<int:image_id>/', views.get_post_data, name='get_post_data'),
    path('post-comment/<int:image_id>/', views.post_comment, name='post_comment'),
]
