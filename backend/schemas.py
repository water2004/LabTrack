from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class EquipmentBase(BaseModel):
    asset_code: Optional[str] = None # 改为可选
    name: str
    location: Optional[str] = None
    manager: Optional[str] = None

class EquipmentCreate(EquipmentBase):
    pass

class Equipment(EquipmentBase):
    id: int
    uuid: str # 必须返回 uuid
    image_path: Optional[str] = None
    status: int
    class Config:
        from_attributes = True

class ExperimentStart(BaseModel):
    device_ids: List[int]
    notes: Optional[str] = None

class ExperimentStop(BaseModel):
    device_ids: List[int]

class AdminAuth(BaseModel):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PresetBase(BaseModel):
    name: str
    device_ids: str
    notes: Optional[str] = None

class PresetCreate(PresetBase):
    pass

class Preset(PresetBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True
