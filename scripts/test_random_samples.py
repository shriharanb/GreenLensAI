import os
import sys
import random

# Add project root and backend to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../"))
sys.path.append(os.path.join(project_root, "backend"))

try:
    from app.services.vision_service import predict_image
    print("✅ Imported vision_service successfully.")
except ImportError as e:
    print(f"❌ Failed to import vision_service: {e}")
    sys.exit(1)

DATASET_DIR = os.path.join(project_root, "data/raw_documents/DataSets")

def test_random_images(n=10):
    print(f"\n🎯 Testing {n} random images from the dataset...")
    
    # Collect all image paths
    all_images = []
    for root, dirs, files in os.walk(DATASET_DIR):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                all_images.append(os.path.join(root, file))
    
    if not all_images:
        print("❌ No images found in dataset.")
        return

    # Pick n random images
    samples = random.sample(all_images, min(len(all_images), n))

    print("-" * 80)
    print(f"{'True Label':<25} | {'Prediction':<25} | {'Confidence':<10} | {'Status'}")
    print("-" * 80)

    correct_count = 0
    for img_path in samples:
        # Extract true label from folder name
        true_label = os.path.basename(os.path.dirname(img_path))
        
        try:
            result = predict_image(img_path)
            pred_label = result["prediction"]
            conf = result["confidence"]
            
            status = "✅ MATCH" if pred_label == true_label else "❌ MISMATCH"
            if pred_label == true_label:
                correct_count += 1
                
            print(f"{true_label[:25]:<25} | {pred_label[:25]:<25} | {conf:.4f}     | {status}")
        except Exception as e:
            print(f"Error testing {img_path}: {e}")

    print("-" * 80)
    print(f"Final Score: {correct_count}/{len(samples)} ({ (correct_count/len(samples))*100 }%)")

if __name__ == "__main__":
    test_random_images(15)
