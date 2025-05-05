import torch
import torchvision.models as models
import torchvision.transforms as transforms

from PIL import Image as PILImage
import numpy as np
import os

from diffusers import DiffusionPipeline
from django.conf import settings
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Currently used device: {device.upper()}")

model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
model.fc = torch.nn.Identity()
model.to(device)
model.eval()
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

pipeline = DiffusionPipeline.from_pretrained(
    "segmind/tiny-sd",
    torch_dtype=torch.float16,
    local_files_only=True  
)
pipeline.to(device)
pipeline.enable_attention_slicing()
print("Pipeline loaded on", device)

def generate_embedding(image_path: str):
    img = PILImage.open(image_path).convert('RGB')
    input_tensor = transform(img).unsqueeze(0).to(device)
    with torch.inference_mode():
        features = model(input_tensor).cpu().numpy()[0]
    return features.tolist()

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return dot / (norm_a * norm_b + 1e-10)

def generate_from_prompt(prompt, name):
    with torch.inference_mode():
        image = pipeline(prompt, num_inference_steps=25).images[0]

    filename = f"{name}.png"
    relative_path = os.path.join('images', filename)
    media_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    os.makedirs(os.path.dirname(media_path), exist_ok=True)
    image.save(media_path)

    return relative_path


