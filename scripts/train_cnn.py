import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, Subset, WeightedRandomSampler
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from collections import Counter
import argparse
# from tqdm import tqdm

# Constants
NUM_CLASSES = 11
IMG_SIZE = 224
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(PROJECT_ROOT, "data/raw_documents/DataSets")
SAVE_PATH = os.path.join(PROJECT_ROOT, "models/cnn/best_rice_model.pth")

# class_names should match vision_service.py exactly
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

class RiceDiseaseDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.classes = class_names  # Use explicit list
        self.class_to_idx = {cls: i for i, cls in enumerate(self.classes)}
        self.samples = []

        for cls in self.classes:
            class_path = os.path.join(root_dir, cls)
            if not os.path.isdir(class_path): continue
            label = self.class_to_idx[cls]
            for img_name in os.listdir(class_path):
                if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.samples.append((os.path.join(class_path, img_name), label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        image = Image.open(path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, torch.tensor(label, dtype=torch.long)

def train(mini=False, sample_limit=None, epochs=5):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 Training on: {device}")

    # Transforms
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomResizedCrop(IMG_SIZE),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # Dataset
    full_dataset = RiceDiseaseDataset(DATASET_DIR, transform=train_transform)
    
    # Split
    indices = list(range(len(full_dataset)))
    np.random.shuffle(indices)
    split = int(0.8 * len(full_dataset))
    train_indices, val_indices = indices[:split], indices[split:]

    if mini or sample_limit:
        limit = 100 if mini and not sample_limit else sample_limit
        print(f"⚠️ Sampling up to {limit} images per class for training...")
        train_indices_subset = []
        counts = {i: 0 for i in range(NUM_CLASSES)}
        for idx in train_indices:
            label = full_dataset.samples[idx][1]
            if counts[label] < limit:
                train_indices_subset.append(idx)
                counts[label] += 1
        train_indices = train_indices_subset
        if mini:
            epochs = 2 # Shorter for mini
        print(f"📍 Training Subset Size: {len(train_indices)}")

    train_subset = Subset(full_dataset, train_indices)
    val_subset = Subset(RiceDiseaseDataset(DATASET_DIR, transform=val_transform), val_indices)

    # Balanced Sampler
    train_labels = [full_dataset.samples[i][1] for i in train_indices]
    label_counts = Counter(train_labels)
    # MODERATED WEIGHTS (Square Root)
    class_weights = {cls: 1.0 / np.sqrt(count) for cls, count in label_counts.items()}
    weights = [class_weights[label] for label in train_labels]
    sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)

    train_loader = DataLoader(train_subset, batch_size=16, sampler=sampler, num_workers=2)
    val_loader = DataLoader(val_subset, batch_size=16, shuffle=False, num_workers=2)

    # Model: MobileNetV2 is faster on CPU
    print("🏗️ Creating MobileNetV2 model...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.last_channel, NUM_CLASSES)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.001)
    
    best_acc = 0.0
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        print(f"\nEpoch {epoch+1}/{epochs}")
        
        for i, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            if i % 10 == 0:
                print(f"  Batch {i}/{len(train_loader)} - Loss: {loss.item():.4f}")

        # Val
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        val_acc = 100 * correct / total
        print(f"⭐ Val Accuracy: {val_acc:.2f}%")

        if val_acc > best_acc:
            best_acc = val_acc
            os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
            torch.save(model.state_dict(), SAVE_PATH)
            print(f"✅ Best Model Saved with {val_acc:.2f}% accuracy")

    print("\n🎉 Training Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mini", action="store_true", help="Train on a small subset for baseline")
    parser.add_argument("--sample_limit", type=int, default=None, help="Limit images per class for training")
    parser.add_argument("--epochs", type=int, default=5)
    args = parser.parse_args()
    
    train(mini=args.mini, sample_limit=args.sample_limit, epochs=args.epochs)
