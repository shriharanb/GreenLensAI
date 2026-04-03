import torch
import torch.nn as nn
import torchvision.models as models
from PIL import Image
import numpy as np
import os
import albumentations as A
from albumentations.pytorch import ToTensorV2

# -------------------------
# Configuration
# -------------------------

NUM_CLASSES = 11
MODEL_PATH = "models/cnn/best_rice_model.pth"  # point to the new trained model

class_names = [
    "Bacterial Leaf Blight",      # 0
    "Blast",                      # 1
    "Brown Spot",                 # 2
    "Healthy Rice Leaf",          # 3
    "Leaf scald",                 # 4
    "Narrow Brown Leaf Spot",     # 5
    "Sheath Blight",              # 6
    "Tungro virus",               # 7
    "grassy stunt virus",         # 8
    "ragged stunt virus",         # 9
    "yellow mottle1 virus"        # 10
]

# -------------------------
# Device
# -------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# -------------------------
# Model Loading (Load Once)
# -------------------------

def load_model():
    """
    Loads the ResNet18 model with custom final layer and weights.
    """
    print("🔄 Starting CNN Model loading...")
    try:
        # Determine absolute path for model file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        full_model_path = os.path.join(project_root, MODEL_PATH)

        print(f"📂 Looking for weights at: {full_model_path}")
        if not os.path.exists(full_model_path):
            print(f"⚠️ Warning: Model weights not found at {full_model_path}. Prediction will be unavailable.")
            return None

        # Load MobileNetV2 (used for efficiency)
        print("🏗️ Creating MobileNetV2 architecture...")
        model = models.mobilenet_v2(weights=None)
        
        # Modify the classifier to match the number of classes (11)
        model.classifier[1] = nn.Linear(model.last_channel, NUM_CLASSES)

        # Load the custom state dict
        print(f"📥 Loading state dict from {full_model_path}...")
        state_dict = torch.load(full_model_path, map_location=device)
        print("🔗 Applying state dict to model...")
        model.load_state_dict(state_dict)
        
        print(f"🚀 Moving model to {device}...")
        model = model.to(device)
        model.eval()
        print(f"✅ CNN Model loaded successfully!")
        return model

    except Exception as e:
        print(f"❌ Error loading CNN Model: {e}")
        return None

# Global model instance
model = load_model()

# -------------------------
# Image Transform (must match training val_transform)
# -------------------------

IMG_SIZE = 224
transform = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.Normalize(),  # ImageNet defaults: mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]
    ToTensorV2(),
])

# -------------------------
# Prediction Function
# -------------------------

def predict_image(image_path: str):
    print(f"🖼️ Predicting image: {image_path}")
    image = Image.open(image_path).convert("RGB")
    image = np.array(image)  # Convert PIL to numpy for Albumentations
    image = transform(image=image)["image"]
    image = image.unsqueeze(0).to(device)

    print("🧠 Running inference...")
    with torch.no_grad():
        outputs = model(image)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)

    return {
        "prediction": class_names[predicted.item()],
        "confidence": float(confidence.item())
    }