from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SystemConfig(Base):
    __tablename__ = "system_config"
    key = Column(String, primary_key=True, index=True)
    value = Column(String)

class Equipment(Base):
    __tablename__ = "equipments"
    id = Column(Integer, primary_key=True, index=True)
    asset_code = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    image_path = Column(String, nullable=True)
    location = Column(String, nullable=True)
    manager = Column(String, nullable=True)
    status = Column(Integer, default=0) # 0: idle, 1: in use, 2: borrowed

class ActiveSession(Base):
    __tablename__ = "active_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    equipment_id = Column(Integer, ForeignKey("equipments.id"))
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    group_id = Column(String, nullable=True) # UUID for grouped experiments

class UsageRecord(Base):
    __tablename__ = "usage_records"
    id = Column(Integer, primary_key=True, index=True)
    asset_code = Column(String)
    device_name = Column(String)
    user_name = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime, default=datetime.datetime.utcnow)
    duration = Column(Integer) # in seconds

class Preset(Base):
    __tablename__ = "presets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    device_ids = Column(String) # Comma separated IDs: "1,2,3"
