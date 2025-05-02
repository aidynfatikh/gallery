from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
import os, json
from .models import Image
from .helpers import generate_embedding_from_bytes, generate_embedding, cosine_similarity, generate_image_from

@csrf_exempt
def image_list(request):
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

    # Save to Cloudinary or default storage
    new_image = Image.objects.create(image=uploaded_file, is_generated=False)

    # Read file bytes from storage
    with new_image.image.open('rb') as f:
        file_bytes = f.read()

    # Generate and save embedding
    embedding = generate_embedding_from_bytes(file_bytes)
    new_image.embedding = embedding
    new_image.save()

    return JsonResponse({'status': 'uploaded'})

@csrf_exempt
def delete_image(request, image_id):
    if request.method != 'DELETE':
        return HttpResponseNotAllowed(['DELETE'])
    img = get_object_or_404(Image, id=image_id)
    # Remove file from storage
    img.image.delete()
    img.delete()
    return JsonResponse({'status': 'deleted'})

@csrf_exempt
def search_by_image(request):
    if request.method != 'POST' or 'image' not in request.FILES:
        return JsonResponse({'error': 'No image uploaded'}, status=400)
    # temporarily save query image
    temp_file = request.FILES['image']
    temp_path = default_storage.save('temp_query', temp_file)
    with default_storage.open(temp_path, 'rb') as f:
        query_bytes = f.read()
    default_storage.delete(temp_path)

    query_vec = generate_embedding_from_bytes(query_bytes)
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

    # Create placeholder record to get ID
    temp = Image.objects.create(image='temp', is_generated=True)
    # Generate and save image to MEDIA_ROOT/images/generated_<id>.png
    relative_path = generate_image_from(prompt, temp.id)
    # Delete placeholder and create real record
    temp.delete()
    new_img = Image.objects.create(image=relative_path, is_generated=True)

    # Compute embedding from saved file
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
