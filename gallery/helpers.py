import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image as PILImage
import numpy as np
from diffusers import DiffusionPipeline
from django.conf import settings
import os

device = "cuda" if torch.cuda.is_available() else "cpu"
model = models.resnet18(weights="ResNet18_Weights.IMAGENET1K_V1")
model.fc = torch.nn.Identity()  
model = model.to(device)
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

from PIL import Image as PILImage
import io

def generate_embedding_from_pil(img: PILImage.Image) -> list:
    input_tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        features = model(input_tensor).cpu().numpy()[0]
    return features.tolist()


def generate_embedding_from_bytes(bts: bytes) -> list:
    img = PILImage.open(io.BytesIO(bts)).convert('RGB')
    return generate_embedding_from_pil(img)


def generate_embedding(image_path: str) -> list:
    img = PILImage.open(image_path).convert('RGB')
    return generate_embedding_from_pil(img)

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return dot / (norm_a * norm_b + 1e-10)  # small term to avoid division by zero

def generate_image_from(prompt, id):
    pipeline = DiffusionPipeline.from_pretrained("segmind/tiny-sd", torch_dtype=torch.float16)    
    pipeline.to("cuda")

    image = pipeline(prompt).images[0]
    filename = f"images/generated_{id}.png"
    media_path = os.path.join(settings.MEDIA_ROOT, filename)

    os.makedirs(os.path.dirname(media_path), exist_ok=True)
    image.save(media_path)

    return os.path.join("images", f"generated_{id}.png")
    