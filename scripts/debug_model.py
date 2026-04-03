import torch
import torch.nn as nn
import torchvision.models as models
import os
import sys

# Add project root and backend to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../"))
sys.path.append(os.path.join(project_root, "backend"))

from app.services.vision_service import class_names, MODEL_PATH, transform

device = torch.device("cpu")

def debug_model():
    full_model_path = os.path.join(project_root, MODEL_PATH)
    print(f"Loading from: {full_model_path}")

    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 11)
    
    state_dict = torch.load(full_model_path, map_location=device)
    
    # Check if state_dict is actually a state dict or a full model/something else
    if not isinstance(state_dict, dict):
        print(f"❌ Loaded object is not a dict, it's a {type(state_dict)}")
    else:
        print(f"✅ Loaded object is a dict with {len(state_dict)} keys")
        sample_keys = list(state_dict.keys())[:5]
        print(f"Sample keys: {sample_keys}")
    
    load_result = model.load_state_dict(state_dict, strict=False)
    print(f"Load result: {load_result}")

    model.eval()

    # Create dummy input
    dummy_input = torch.randn(1, 3, 224, 224)
    with torch.no_grad():
        output = model(dummy_input)
        probs = torch.softmax(output, dim=1)
        conf, pred = torch.max(probs, 1)

    print(f"\nRaw output logits: {output}")
    print(f"Probabilities: {probs}")
    print(f"Prediction: {class_names[pred.item()]} ({conf.item():.4f})")

    # Check last layer weights
    fc_weights = state_dict.get('fc.weight')
    if fc_weights is not None:
        print(f"\nFC weights shape: {fc_weights.shape}")
        # Check if one class has much higher bias/weights
        fc_bias = state_dict.get('fc.bias')
        if fc_bias is not None:
            print(f"FC bias: {fc_bias}")

if __name__ == "__main__":
    debug_model()
