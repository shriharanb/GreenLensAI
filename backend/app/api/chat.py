from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.config import get_db_connection

router = APIRouter()

class ChatMessage(BaseModel):
    farmer_id: str
    message_type: str # 'user' or 'bot'
    content: str = None
    image_path: str = None

class MessageResponse(BaseModel):
    id: int
    farmer_id: str
    message_type: str
    content: str = None
    image_path: str = None
    timestamp: str

@router.get("/history/{farmer_id}", response_model=List[MessageResponse])
def get_chat_history(farmer_id: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, farmer_id, message_type, content, image_path, timestamp::text FROM chat_history WHERE farmer_id = %s ORDER BY timestamp ASC",
            (farmer_id,)
        )
        rows = cur.fetchall()
        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "farmer_id": row[1],
                "message_type": row[2],
                "content": row[3],
                "image_path": row[4],
                "timestamp": row[5]
            })
        return messages
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()

@router.post("/save")
def save_message(msg: ChatMessage):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO chat_history (farmer_id, message_type, content, image_path) VALUES (%s, %s, %s, %s) RETURNING id",
            (msg.farmer_id, msg.message_type, msg.content, msg.image_path)
        )
        conn.commit()
        msg_id = cur.fetchone()[0]
        return {"id": msg_id, "message": "Message saved successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
