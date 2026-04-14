from sqlalchemy import Column, String, Boolean, JSON, DateTime, Float, Text, Integer, ForeignKey
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class UserAccount(Base):
    __tablename__ = "user_accounts"

    id = Column(String, primary_key=True, default=uuid_str)
    email = Column(String, unique=True, index=True, nullable=False)
    session_token = Column(String, unique=True, index=True, nullable=False, default=uuid_str)
    registered_ip = Column(String, index=True, nullable=True)
    free_generations_limit = Column(Integer, default=3)
    free_generations_used = Column(Integer, default=0)
    license_code_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EmailLoginCode(Base):
    __tablename__ = "email_login_codes"

    id = Column(String, primary_key=True, default=uuid_str)
    email = Column(String, unique=True, index=True, nullable=False)
    code_hash = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    send_count = Column(Integer, default=1)
    verify_attempts = Column(Integer, default=0)
    request_ip = Column(String, nullable=True, index=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LicenseCode(Base):
    __tablename__ = "license_codes"

    id = Column(String, primary_key=True, default=uuid_str)
    code = Column(String, unique=True, index=True, nullable=False)  # NYAI-XXXX-XXXX-XXXX
    max_images = Column(Integer, nullable=True)  # null = unlimited
    images_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    note = Column(String, nullable=True)
    owner_user_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserAPIConfig(Base):
    __tablename__ = "user_api_configs"

    id = Column(String, primary_key=True, default=uuid_str)
    license_code_id = Column(String, ForeignKey("license_codes.id"), nullable=False, index=True)
    provider_preset_id = Column(String, nullable=False)  # preset id or "custom"
    display_name = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    api_protocol = Column(String, nullable=False, default="OpenAI")  # "OpenAI" | "Google API"
    is_active = Column(Boolean, default=True)
    purpose = Column(String, default="generation")  # "generation" | "vision"
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id = Column(String, primary_key=True, default=uuid_str)
    user_id = Column(String, nullable=True, index=True)
    license_code_id = Column(String, ForeignKey("license_codes.id"), nullable=True, index=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    market = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    cost = Column(Float, default=0.0)
    images = Column(JSON, default=[])
    product_dna = Column(Text, nullable=True)  # AI提取的产品DNA描述
    persona_id = Column(String, nullable=True)  # 使用的模特设定ID
    selected_plans = Column(JSON, nullable=True)  # [{"market":"germany","plan":"A"}, ...]
    model_mode = Column(String, default="ai_generate")  # "ai_generate" 或 "reference_model"
    plan_results = Column(JSON, nullable=True)  # [{"market":"germany","plan":"A","image_url":"..."}, ...]
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(String, primary_key=True, default=uuid_str)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
