import os
import sys
import torch
import torch.nn as nn
from PIL import Image
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2

# Add project root and backend to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../"))
sys.path.append(os.path.join(project_root, "backend"))

from app.services.vision_service import class_names, MODEL_PATH, NUM_CLASSES

device = torch.device("cpu")

def load_debug_model():
    model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=False)
    model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
    full_path = os.path.join(project_root, MODEL_PATH)
    model.load_state_dict(torch.load(full_path, map_location=device))
    model.eval()
    return model

def trace_predictions():
    model = load_debug_model()
    
    transform = A.Compose([
        A.Resize(224, 224),
        A.Normalize(),
        ToTensorV2(),
    ])

    dataset_dir = os.path.join(project_root, "data/raw_documents/DataSets")
    
    for cls in sorted(os.listdir(dataset_dir)):
        cls_path = os.path.join(dataset_dir, cls)
        if not os.path.isdir(cls_path): continue
        
        images = [f for f in os.listdir(cls_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not images: continue
        
        print(f"\n📁 Class: {cls}")
        for i in range(min(2, len(images))):
            img_path = os.path.join(cls_path, images[i])
            image = Image.open(img_path).convert("RGB")
            image_np = np.array(image)
            input_tensor = transform(image=image_np)["image"].unsqueeze(0)
            
            with torch.no_grad():
                output = model(input_tensor)
                probs = torch.softmax(output, dim=1)[0]
                
            top_probs, top_idxs = torch.topk(probs, 3)
            
            print(f"  🖼️ {images[i]}:")
            for p, idx in zip(top_probs, top_idxs):
                print(f"    - {class_names[idx.item()]:<25}: {p.item():.4f}")

if __name__ == "__main__":
    trace_predictions()
