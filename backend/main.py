from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import base64
import datetime
import requests
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

# --- 系统配置助手 (基于 SystemConfig 键值表) ---
def get_config(db: Session, key: str, default: str = None):
    row = db.query(models.SystemConfig).filter(models.SystemConfig.key == key).first()
    return row.value if row else default

def set_config(db: Session, key: str, value: str):
    row = db.query(models.SystemConfig).filter(models.SystemConfig.key == key).first()
    if row:
        row.value = value
    else:
        db.add(models.SystemConfig(key=key, value=value))

# --- User APIs ---

@app.post("/auth/login", response_model=schemas.Token)
def login(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please contact admin.")
    # In a real app, we'd issue a real JWT. Here we use username as token for simplicity.
    return {"access_token": user.username, "token_type": "bearer"}

# --- 公开配置 (前台据此决定是否显示 AI 功能) ---
@app.get("/config/public")
def get_public_config(db: Session = Depends(get_db)):
    return {
        "vision_enabled": get_config(db, "vision_enabled", "false") == "true"
    }

# --- AI 视觉识别 ---
def _build_chat_url(base_url: str) -> str:
    """将管理员配置的端点 URL 规范为 chat/completions 地址。"""
    url = (base_url or "").strip().rstrip("/")
    if not url:
        raise HTTPException(status_code=500, detail="Vision API URL not configured")
    if url.endswith("/chat/completions"):
        return url
    return f"{url}/chat/completions"

@app.post("/vision/recognize")
async def vision_recognize(
    mode: str = Form(...),  # 'name' 识别设备名称, 'code' 识别资产编号
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if get_config(db, "vision_enabled", "false") != "true":
        raise HTTPException(status_code=403, detail="视觉识别功能未开启")

    api_url = get_config(db, "vision_api_url")
    api_key = get_config(db, "vision_api_key")
    model = get_config(db, "vision_model") or "gpt-4o-mini"
    if not api_url or not api_key:
        raise HTTPException(status_code=400, detail="视觉模型尚未配置完整")

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="图片为空")
    mime = image.content_type or "image/jpeg"
    b64 = base64.b64encode(raw).decode("utf-8")

    if mode == "name":
        prompt = (
            "这是一张实验室仪器/设备的照片。请仅返回该设备的中文名称（如：恒温摇床、离心机、电子天平），"
            "不要包含型号、品牌、标点或任何多余文字。若无法确定，返回最贴近的通用设备名称。"
        )
    elif mode == "code":
        prompt = (
            "这是一张设备资产标签的照片，条形码附近通常印有一串数字或字母数字组成的资产编号。"
            "请仅返回该编号本身（连续的字符），不要包含空格、换行、说明文字或其他内容。"
            "若图中存在多个编号，返回与条形码关联的主编号。"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": 60,
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        resp = requests.post(_build_chat_url(api_url), json=payload, headers=headers, timeout=60)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"无法连接视觉服务: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"视觉服务返回错误 ({resp.status_code}): {resp.text[:200]}")

    try:
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise HTTPException(status_code=502, detail="无法解析视觉服务返回结果")

    result = (text or "").strip().strip('`"\'').strip()
    if not result:
        raise HTTPException(status_code=422, detail="未能识别出有效内容")
    return {"result": result}

@app.get("/devices", response_model=List[schemas.Equipment])
def get_devices(q: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Equipment)
    if q:
        query = query.filter(
            (models.Equipment.name.contains(q)) | 
            (models.Equipment.asset_code.contains(q)) |
            (models.Equipment.uuid.contains(q))
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
    username: str = Form(None), # 接收当前操作者用户名用于校验
    db: Session = Depends(get_db)
):
    device = db.query(models.Equipment).filter(models.Equipment.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 权限校验：只有当前负责人或管理员（简单处理，如果提供了username）可以修改
    if username and device.manager and device.manager != username:
         # 如果不是负责人，检查是否是管理员（这里简单对比，实际可更严谨）
         if username != "admin": 
             raise HTTPException(status_code=403, detail="Only the manager or admin can update this device")

    if name is not None: device.name = name
    
    # 资产编号修改校验
    if asset_code is not None:
        if asset_code != "" and asset_code != device.asset_code:
            existing = db.query(models.Equipment).filter(models.Equipment.asset_code == asset_code).first()
            if existing:
                raise HTTPException(status_code=400, detail="Asset code already exists")
            device.asset_code = asset_code
        elif asset_code == "":
            device.asset_code = None

    if location is not None: device.location = location
    
    # 负责人转让校验
    if manager is not None:
        if manager != "":
            # 检查目标用户是否存在
            target_user = db.query(models.User).filter(models.User.username == manager).first()
            if not target_user:
                raise HTTPException(status_code=400, detail=f"User '{manager}' does not exist")
        device.manager = manager

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

# --- 系统设置 / AI 视觉 ---
@app.get("/admin/config")
def get_admin_config(db: Session = Depends(get_db)):
    api_key = get_config(db, "vision_api_key", "")
    return {
        "vision_enabled": get_config(db, "vision_enabled", "false") == "true",
        "vision_api_url": get_config(db, "vision_api_url", ""),
        "vision_model": get_config(db, "vision_model", ""),
        # 不回传明文 Key，仅告知是否已设置
        "vision_api_key_set": bool(api_key),
    }

@app.post("/admin/config")
def update_admin_config(data: schemas.VisionConfigUpdate, db: Session = Depends(get_db)):
    set_config(db, "vision_enabled", "true" if data.vision_enabled else "false")
    set_config(db, "vision_api_url", (data.vision_api_url or "").strip())
    set_config(db, "vision_model", (data.vision_model or "").strip())
    # 仅当传入非空 Key 时更新，留空表示保持原值
    if data.vision_api_key:
        set_config(db, "vision_api_key", data.vision_api_key.strip())
    db.commit()
    return {"status": "success"}

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
    asset_code: str = Form(None), # 改为可选
    location: str = Form(None), 
    manager: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # 使用完整 UUID 确保绝对唯一性
    device_uuid = str(uuid.uuid4()).upper() 
    
    # 如果提供了资产编号，检查唯一性
    if asset_code:
        existing = db.query(models.Equipment).filter(models.Equipment.asset_code == asset_code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Asset code already exists")

    image_path = None
    if image:
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        image_path = os.path.join(UPLOAD_DIR, file_name)
        with open(image_path, "wb") as buffer:
            buffer.write(image.file.read())
        image_path = f"/static/uploads/{file_name}"

    device = models.Equipment(
        uuid=device_uuid, # 系统自动分配完整 UUID
        name=name,
        asset_code=asset_code if asset_code else None,
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

@app.delete("/admin/devices/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(models.Equipment).filter(models.Equipment.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 检查是否有正在进行的实验使用该设备
    active = db.query(models.ActiveSession).filter(models.ActiveSession.equipment_id == device_id).first()
    if active:
        raise HTTPException(status_code=400, detail="Cannot delete a device that is currently in use")
    
    db.delete(device)
    db.commit()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
