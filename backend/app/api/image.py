from fastapi import APIRouter, File, UploadFile, HTTPException, Form
import os
import shutil
import uuid
from app.services.vision_service import predict_image
from app.config import get_db_connection

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/predict")
async def predict_crop_disease(
    farmer_id: str = Form(...),
    file: UploadFile = File(...)
):
    # 1. Save File
    file_ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 2. Predict
        result = predict_image(file_path)
        
        # 3. Save to Chat History
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            # Save user's image message
            cur.execute(
                "INSERT INTO chat_history (farmer_id, message_type, content, image_path) VALUES (%s, %s, %s, %s)",
                (farmer_id, "user", "Uploaded an image for diagnosis", file_path)
            )
            # Save bot's response message
            bot_content = f"Diagnosis: {result['prediction']} (Confidence: {result['confidence']:.2%})"
            cur.execute(
                "INSERT INTO chat_history (farmer_id, message_type, content) VALUES (%s, %s, %s)",
                (farmer_id, "bot", bot_content)
            )
            conn.commit()
            cur.close()
            conn.close()
            
        return {
            "farmer_id": farmer_id,
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "image_url": file_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
