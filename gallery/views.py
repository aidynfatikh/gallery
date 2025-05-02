from django.shortcuts import render, redirect
from .models import Image
from .helpers import generate_embedding, cosine_similarity, generate_image_from
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.conf import settings
import numpy as np
import json
import os

def image_list(request):
    images = Image.objects.all().order_by('-uploaded_at')
    data = [
        {
            'id': image.id,
            'image_url': image.image.url,
            'uploaded_at': image.uploaded_at,
            'is_generated': image.is_generated,
        } for image in images
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
def upload_image(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("image")
        if uploaded_file:
            new_image = Image(image=uploaded_file, is_generated=False)
            new_image.save()

            new_image.embedding = generate_embedding(new_image.image.path)
            new_image.save()

            return JsonResponse({'status': 'uploaded'})
    return JsonResponse({'error': 'No image uploaded'}, status=400)


@csrf_exempt
def delete_image(request, image_id):
    if request.method == "DELETE":
        try:
            image = Image.objects.get(id=image_id)
            image.image.delete()  # delete the file
            image.delete()        # delete the DB entry
            return JsonResponse({'status': 'deleted'})
        except Image.DoesNotExist:
            return JsonResponse({'error': 'Image not found'}, status=404)
    return HttpResponseNotAllowed(['DELETE'])

@csrf_exempt
def search_by_image(request):
    if request.method == 'POST' and 'image' in request.FILES:
        temp_file = request.FILES['image']
        temp_path = default_storage.save('temp/query.jpg', temp_file)
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)

        query_vec = generate_embedding(full_path)
        default_storage.delete(temp_path)

        images = Image.objects.exclude(embedding=None)
        if not images.exists():
            print("doesnt exist")
            return JsonResponse([], safe=False)

        similarities = [
            cosine_similarity(query_vec, img.embedding) for img in images
        ]

        top_indices = np.argsort(similarities)[::-1]
        image_list = list(images)
        top_images = [image_list[int(i)] for i in top_indices]

        data = [{
            'id': img.id,
            'image_url': request.build_absolute_uri(img.image.url),
            'uploaded_at': img.uploaded_at,
            'is_generated': img.is_generated,
        } for img in top_images]

        return JsonResponse(data, safe=False)
    return JsonResponse({'error': 'No image uploaded'}, status=400)

@csrf_exempt
def generate_image(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        prompt = data.get('prompt')

        if not prompt:
            return JsonResponse({'error': 'Prompt required'}, status=400)

        temp = Image.objects.create(image='temp.jpg', is_generated=True)
        image_path = generate_image_from(prompt, temp.id)  # returns local file path
        temp.delete()

        new_image = Image.objects.create(image=image_path,is_generated=True)
        new_image.embedding = generate_embedding(new_image.image.path)
        new_image.save()

        return JsonResponse({
            'id': new_image.id,
            'image_url': request.build_absolute_uri(new_image.image.url),
            'uploaded_at': new_image.uploaded_at,
            'is_generated': new_image.is_generated,
        })



