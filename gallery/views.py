from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string
from django.conf import settings
import os, json
import uuid

from .models import Image
from .helpers import generate_embedding, cosine_similarity, generate_from_prompt

@csrf_exempt
def list_images(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    images = Image.objects.all().order_by('-uploaded_at')
    data = [
        {
            'id': img.id,
            'image_url': img.image.url,
            'uploaded_at': img.uploaded_at,
            'is_generated': img.is_generated,
        }
        for img in images
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
def upload_image(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    uploaded_file = request.FILES.get('image')
    if not uploaded_file:
        return JsonResponse({'error': 'No image uploaded'}, status=400)

    new_image = Image.objects.create(image=uploaded_file, is_generated=False)
    new_image.embedding = generate_embedding(new_image.image.path)
    new_image.save()

    return JsonResponse({'status': 'uploaded'})


@csrf_exempt
def delete_image(request, image_id):
    if request.method != 'DELETE':
        return HttpResponseNotAllowed(['DELETE'])
    img = get_object_or_404(Image, id=image_id)
    img.image.delete()
    img.delete()
    return JsonResponse({'status': 'deleted'})


@csrf_exempt
def search_by_image(request):
    if request.method != 'POST' or 'image' not in request.FILES:
        return JsonResponse({'error': 'No image uploaded'}, status=400)

    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    uploaded_file = request.FILES['image']
    filename = get_random_string(12) + "_" + uploaded_file.name
    temp_path = os.path.join(temp_dir, filename)

    with open(temp_path, 'wb+') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    try:
        query_vec = generate_embedding(temp_path)
    except Exception as e:
        os.remove(temp_path)
        return JsonResponse({'error': f'Failed to process image: {str(e)}'}, status=400)

    os.remove(temp_path)

    imgs = Image.objects.exclude(embedding=None)
    sims = [(img, cosine_similarity(query_vec, img.embedding)) for img in imgs]
    sims.sort(key=lambda x: x[1], reverse=True)

    data = [
        {
            'id': img.id,
            'image_url': request.build_absolute_uri(img.image.url),
            'uploaded_at': img.uploaded_at,
            'is_generated': img.is_generated,
        }
        for img, _ in sims
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
def generate_image(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    if not prompt:
        return JsonResponse({'error': 'Prompt required'}, status=400)

    relative_path = generate_from_prompt(prompt, uuid.uuid4().hex)
    new_img = Image.objects.create(image=relative_path, is_generated=True)

    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    emb = generate_embedding(full_path)
    new_img.embedding = emb
    new_img.save()

    return JsonResponse({
        'id': new_img.id,
        'image_url': request.build_absolute_uri(new_img.image.url),
        'uploaded_at': new_img.uploaded_at,
        'is_generated': new_img.is_generated,
    })