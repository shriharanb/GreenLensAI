from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from app.config import get_db_connection

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class FarmerRegister(BaseModel):
    farmer_id: str
    phone: str
    email: str = None
    recovery_answer: str
    password: str

class FarmerLogin(BaseModel):
    farmer_id: str
    password: str

@router.post("/register")
def register_farmer(farmer: FarmerRegister):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cur = conn.cursor()
    try:
        # Check if user exists
        cur.execute("SELECT 1 FROM farmers WHERE farmer_id = %s", (farmer.farmer_id,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Farmer ID already exists")
        
        # Hash password
        hashed_password = pwd_context.hash(farmer.password)
        
        # Insert user
        cur.execute(
            "INSERT INTO farmers (farmer_id, phone, email, recovery_answer, password_hash) VALUES (%s, %s, %s, %s, %s)",
            (farmer.farmer_id, farmer.phone, farmer.email, farmer.recovery_answer, hashed_password)
        )
        conn.commit()
        return {"message": "Farmer registered successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()

@router.post("/login")
def login_farmer(farmer: FarmerLogin):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cur = conn.cursor()
    try:
        cur.execute("SELECT password_hash FROM farmers WHERE farmer_id = %s", (farmer.farmer_id,))
        record = cur.fetchone()
        if not record or not pwd_context.verify(farmer.password, record[0]):
            raise HTTPException(status_code=401, detail="Invalid Farmer ID or password")
        
        return {"message": "Login successful", "farmer_id": farmer.farmer_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
