from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.crypto import get_random_string
from django.conf import settings
import os, json
import uuid

from .models import Image, Comment
from .helpers import generate_embedding, cosine_similarity, generate_from_prompt

@csrf_exempt
def list_images(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    liked = request.session.get('liked_images', [])
    images = Image.objects.all().order_by('-uploaded_at')
    data = []
    for img in images:
        data.append({
            'id': img.id,
            'image_url': img.image.url,
            'uploaded_at': img.uploaded_at,
            'is_generated': img.is_generated,
            'likes': img.likes,
            'already_liked': img.id in liked,
        })
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

    liked_ids = request.session.get('liked_images', [])

    data = [
        {
            'id': img.id,
            'image_url': request.build_absolute_uri(img.image.url),
            'uploaded_at': img.uploaded_at.isoformat(),
            'is_generated': img.is_generated,
            'likes': img.likes,
            'already_liked': img.id in liked_ids,
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

@csrf_exempt
def like_image(request, image_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    liked = request.session.get('liked_images', [])
    img = get_object_or_404(Image, id=image_id)

    if image_id not in liked:
        img.likes += 1
        img.save()
        liked.append(image_id)
        request.session['liked_images'] = liked
        request.session.modified = True
        action = 'liked'
    else:
        action = 'none' 

    return JsonResponse({'likes': img.likes, 'action': action})


@csrf_exempt
def unlike_image(request, image_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    liked = request.session.get('liked_images', [])
    img = get_object_or_404(Image, id=image_id)

    if image_id in liked and img.likes > 0:
        img.likes -= 1
        img.save()
        liked.remove(image_id)
        request.session['liked_images'] = liked
        request.session.modified = True
        action = 'unliked'
    else:
        action = 'none'

    return JsonResponse({'likes': img.likes, 'action': action})

@csrf_exempt
@require_http_methods(['GET'])
def get_post_data(request, image_id):
    img = get_object_or_404(Image, id=image_id)
    comments = [
        {'id': c.id, 'text': c.text, 'created_at': c.created_at}
        for c in img.comments.order_by('created_at')
    ]
    return JsonResponse({
        'id': img.id,
        'image_url': request.build_absolute_uri(img.image.url),
        'likes': img.likes,
        'already_liked': image_id in request.session.get('liked_images', []),
        'comments': comments,
    })

@csrf_exempt
@require_http_methods(['POST'])
def post_comment(request, image_id):
    img = get_object_or_404(Image, id=image_id)
    body = json.loads(request.body.decode('utf-8'))
    text = body.get('text', '').strip()
    if not text:
        return JsonResponse({'error': 'Empty comment'}, status=400)

    comment = Comment.objects.create(image=img, text=text)
    return JsonResponse({
        'id': comment.id,
        'text': comment.text,
        'created_at': comment.created_at,
    })