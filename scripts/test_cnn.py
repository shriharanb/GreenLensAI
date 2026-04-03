import sys
import os
import torch
import numpy as np
from PIL import Image

# Add backend to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../"))
sys.path.append(os.path.join(project_root, "backend"))

try:
    from app.services.vision_service import predict_image, model, class_names
    print("✅ Imported vision_service successfully.")
except ImportError as e:
    print(f"❌ Failed to import vision_service: {e}")
    sys.exit(1)

def test_inference_with_dummy():
    if model is None:
        print("❌ Model is not loaded. Cannot run test.")
        return

    print("\n--- Testing CNN Model with Dummy Image ---")
    
    # Create a dummy image (224x224 RGB)
    dummy_img_path = os.path.join(project_root, "temp_dummy_leaf.png")
    dummy_data = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    Image.fromarray(dummy_data).save(dummy_img_path)
    
    try:
        result = predict_image(dummy_img_path)
        print(f"Prediction result: {result}")
        
        if result['prediction'] in class_names:
            print("✅ Inference logic verified!")
        else:
            print(f"❌ Unexpected prediction label: {result['prediction']}")
            
    except Exception as e:
        print(f"❌ Inference failed: {e}")
    finally:
        if os.path.exists(dummy_img_path):
            os.remove(dummy_img_path)

if __name__ == "__main__":
    test_inference_with_dummy()
