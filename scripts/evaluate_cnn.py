import os
import sys
import random
import time
from collections import defaultdict

# Add project root and backend to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../"))
sys.path.append(os.path.join(project_root, "backend"))

try:
    from app.services.vision_service import predict_image, class_names, model
    print("✅ Imported vision_service successfully.")
except ImportError as e:
    print(f"❌ Failed to import vision_service: {e}")
    sys.exit(1)

DATASET_DIR = os.path.join(project_root, "data/raw_documents/DataSets")
SAMPLE_SIZE_PER_CLASS = 20  # Number of images to test per class

def evaluate():
    if model is None:
        print("❌ Model could not be loaded. Check your DDM.pth path.")
        return

    if not os.path.exists(DATASET_DIR):
        print(f"❌ Dataset directory not found: {DATASET_DIR}")
        return

    results = {
        "overall": {"correct": 0, "total": 0},
        "per_class": defaultdict(lambda: {"correct": 0, "total": 0, "confused_with": defaultdict(int)})
    }

    start_time = time.time()

    print(f"\n🚀 Starting evaluation on {DATASET_DIR}...")
    print(f"📊 Sampling up to {SAMPLE_SIZE_PER_CLASS} images per class.\n")

    # Iterate through each folder (class name)
    for true_label in os.listdir(DATASET_DIR):
        class_path = os.path.join(DATASET_DIR, true_label)
        if not os.path.isdir(class_path):
            continue
        
        # Get all image files
        images = [f for f in os.listdir(class_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            print(f"⚠️ No images found in {true_label}. Skipping.")
            continue

        # Sample images
        sample = random.sample(images, min(len(images), SAMPLE_SIZE_PER_CLASS))
        print(f"📁 Testing class: {true_label} ({len(sample)} samples)")

        for img_name in sample:
            img_path = os.path.join(class_path, img_name)
            try:
                prediction_result = predict_image(img_path)
                pred_label = prediction_result["prediction"]
                
                results["overall"]["total"] += 1
                results["per_class"][true_label]["total"] += 1

                if pred_label == true_label:
                    results["overall"]["correct"] += 1
                    results["per_class"][true_label]["correct"] += 1
                else:
                    results["per_class"][true_label]["confused_with"][pred_label] += 1
            except Exception as e:
                print(f"   ❌ Error predicting {img_name}: {e}")

    end_time = time.time()
    duration = end_time - start_time

    # --- Print Summary Report ---
    print("\n" + "="*50)
    print("      CNN MODEL EVALUATION SUMMARY")
    print("="*50)
    
    overall_acc = (results["overall"]["correct"] / results["overall"]["total"]) * 100 if results["overall"]["total"] > 0 else 0
    print(f"📍 Total Images Tested: {results['overall']['total']}")
    print(f"📍 Overall Accuracy:    {overall_acc:.2f}%")
    print(f"📍 Time Taken:          {duration:.2f} seconds")
    print("-" * 50)
    print(f"{'Class Name':<30} | {'Accuracy':<10}")
    print("-" * 50)

    for cls in sorted(results["per_class"].keys()):
        stats = results["per_class"][cls]
        acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        print(f"{cls:<30} | {acc:.2f}% ({stats['correct']}/{stats['total']})")
        
        # Show top confusion if accuracy is not 100%
        if acc < 100 and stats["confused_with"]:
            sorted_confusion = sorted(stats["confused_with"].items(), key=lambda x: x[1], reverse=True)
            confusion_str = ", ".join([f"{k}({v})" for k, v in sorted_confusion[:2]])
            print(f"   ↳ Mostly confused with: {confusion_str}")

    print("="*50)

if __name__ == "__main__":
    evaluate()
