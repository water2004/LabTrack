from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import datetime
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse

import models, schemas, database
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

# Static files for uploads
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "static/uploads")
DB_FILE = os.getenv("DATABASE_URL", "sqlite:///./labtrack.db").replace("sqlite:///", "")

# 简单的数据库迁移：确保 notes 列存在
def migrate_db():
    import sqlite3
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for table in ['active_sessions', 'usage_records', 'presets']:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN notes TEXT")
            except sqlite3.OperationalError:
                pass # 已经存在则忽略
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration notice: {e}")

migrate_db()

app = FastAPI(title="LabTrack API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="static")

# Auth Helpers (Simple for initial version)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "LabAdmin2024")

def verify_admin(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    return True

# --- User APIs ---

@app.post("/auth/login", response_model=schemas.Token)
def login(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please contact admin.")
    # In a real app, we'd issue a real JWT. Here we use username as token for simplicity.
    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/devices", response_model=List[schemas.Equipment])
def get_devices(q: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Equipment)
    if q:
        query = query.filter(
            (models.Equipment.name.contains(q)) | (models.Equipment.asset_code.contains(q))
        )
    return query.all()

@app.put("/devices/{device_id}")
def update_device(
    device_id: int,
    name: str = Form(None),
    asset_code: str = Form(None),
    location: str = Form(None),
    manager: str = Form(None),
    status: int = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    device = db.query(models.Equipment).filter(models.Equipment.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if name is not None: device.name = name
    if asset_code is not None: device.asset_code = asset_code
    if location is not None: device.location = location
    if manager is not None: device.manager = manager
    if status is not None: device.status = int(status)
    
    if image:
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        image_path = os.path.join(UPLOAD_DIR, file_name)
        with open(image_path, "wb") as buffer:
            buffer.write(image.file.read())
        device.image_path = f"/static/uploads/{file_name}"
    
    db.commit()
    db.refresh(device)
    return device

@app.post("/experiment/start")
def start_experiment(data: schemas.ExperimentStart, username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    group_id = str(uuid.uuid4())
    equipments = db.query(models.Equipment).filter(models.Equipment.id.in_(data.device_ids)).all()
    
    for eq in equipments:
        if eq.status != 0:
            raise HTTPException(status_code=400, detail=f"Device {eq.name} is not idle")
        eq.status = 1
        session = models.ActiveSession(user_id=user.id, equipment_id=eq.id, group_id=group_id, notes=data.notes)
        db.add(session)
    
    db.commit()
    return {"status": "success", "group_id": group_id}

@app.post("/experiment/stop")
def stop_experiment(data: schemas.ExperimentStop, username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")

    sessions = db.query(models.ActiveSession).filter(
        models.ActiveSession.equipment_id.in_(data.device_ids),
        models.ActiveSession.user_id == user.id
    ).all()

    for session in sessions:
        eq = db.query(models.Equipment).filter(models.Equipment.id == session.equipment_id).first()
        if eq:
            eq.status = 0
            # Create usage record
            now = datetime.datetime.utcnow()
            duration = (now - session.start_time).total_seconds()
            record = models.UsageRecord(
                asset_code=eq.asset_code,
                device_name=eq.name,
                user_name=user.username,
                start_time=session.start_time,
                end_time=now,
                duration=int(duration),
                notes=session.notes
            )
            db.add(record)
        db.delete(session)
    
    db.commit()
    return {"status": "success"}

@app.get("/users/me/active")
def get_my_active_devices(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    active_sessions = db.query(models.ActiveSession).filter(models.ActiveSession.user_id == user.id).all()
    device_ids = [s.equipment_id for s in active_sessions]
    devices = db.query(models.Equipment).filter(models.Equipment.id.in_(device_ids)).all()
    return devices

@app.get("/users/me/active-groups")
def get_my_active_groups(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    sessions = db.query(models.ActiveSession).filter(models.ActiveSession.user_id == user.id).all()
    
    groups = {}
    for s in sessions:
        if s.group_id not in groups:
            groups[s.group_id] = {
                "group_id": s.group_id,
                "start_time": s.start_time,
                "notes": s.notes,
                "devices": []
            }
        eq = db.query(models.Equipment).filter(models.Equipment.id == s.equipment_id).first()
        if eq:
            groups[s.group_id]["devices"].append({
                "id": eq.id,
                "name": eq.name,
                "asset_code": eq.asset_code
            })
    
    return list(groups.values())

# --- Preset APIs ---

@app.post("/presets", response_model=schemas.Preset)
def create_preset(data: schemas.PresetCreate, username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    preset = models.Preset(user_id=user.id, name=data.name, device_ids=data.device_ids)
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset

@app.get("/presets", response_model=List[schemas.Preset])
def get_presets(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    return db.query(models.Preset).filter(models.Preset.user_id == user.id).all()

@app.put("/presets/{preset_id}", response_model=schemas.Preset)
def update_preset(preset_id: int, data: schemas.PresetCreate, username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    preset = db.query(models.Preset).filter(models.Preset.id == preset_id, models.Preset.user_id == user.id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    preset.name = data.name
    preset.device_ids = data.device_ids
    preset.notes = data.notes
    db.commit()
    db.refresh(preset)
    return preset

@app.delete("/presets/{preset_id}")
def delete_preset(preset_id: int, username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    preset = db.query(models.Preset).filter(models.Preset.id == preset_id, models.Preset.user_id == user.id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    db.delete(preset)
    db.commit()
    return {"status": "success"}

# --- Admin APIs ---

@app.post("/admin/auth")
def admin_auth(data: schemas.AdminAuth):
    verify_admin(data.password)
    return {"access_token": "admin_token", "token_type": "bearer"}

@app.post("/admin/users")
def add_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = models.User(username=user_data.username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/admin/users", response_model=List[schemas.User])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.post("/admin/devices")
def add_device(
    name: str = Form(...), 
    asset_code: str = Form(...), 
    location: str = Form(None), 
    manager: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    image_path = None
    if image:
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        image_path = os.path.join(UPLOAD_DIR, file_name)
        with open(image_path, "wb") as buffer:
            buffer.write(image.file.read())
        image_path = f"/static/uploads/{file_name}"

    device = models.Equipment(
        name=name,
        asset_code=asset_code,
        location=location,
        manager=manager,
        image_path=image_path,
        status=0
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

@app.get("/admin/records")
def list_records(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    query = db.query(models.UsageRecord)
    if start_date:
        query = query.filter(models.UsageRecord.start_time >= start_date)
    if end_date:
        query = query.filter(models.UsageRecord.end_time <= end_date)
    return query.order_by(models.UsageRecord.end_time.desc()).all()

@app.get("/admin/export")
def export_records(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    query = db.query(models.UsageRecord)
    if start_date:
        query = query.filter(models.UsageRecord.start_time >= start_date)
    if end_date:
        query = query.filter(models.UsageRecord.end_time <= end_date)
    
    records = query.all()
    df = pd.DataFrame([
        {
            "资产编号": r.asset_code,
            "设备名": r.device_name,
            "使用者": r.user_name,
            "开始时间": r.start_time.strftime("%Y-%m-%d %H:%M:%S") if r.start_time else "",
            "结束时间": r.end_time.strftime("%Y-%m-%d %H:%M:%S") if r.end_time else "",
            "时长(秒)": r.duration,
            "备注": r.notes
        } for r in records
    ])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='使用记录')
    
    output.seek(0)
    filename = f"usage_records_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
