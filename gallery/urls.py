from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='gallery/gallery_api.html'), name='home'),
    path('images/', views.image_list, name='image-list'),
    path('upload/', views.upload_image, name='upload-image'),
    path('delete/<int:image_id>/', views.delete_image, name='delete-image'),
    path('search-image/', views.search_by_image, name='search-image'),
    path('generate-image/', views.generate_image, name='generate-image'),

]

