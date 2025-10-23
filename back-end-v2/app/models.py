from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint, Boolean, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime

Base = declarative_base()

class User(Base):
    """Modèle utilisateur pour l'authentification"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    execution_history = relationship("PromptExecutionHistory", back_populates="user", cascade="all, delete-orphan")

class Specialty(Base):
    __tablename__ = "specialties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    icon_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    sub_specialties = relationship("SubSpecialty", back_populates="specialty", cascade="all, delete-orphan")

class SubSpecialty(Base):
    __tablename__ = "sub_specialties"

    id = Column(Integer, primary_key=True, index=True)
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    specialty = relationship("Specialty", back_populates="sub_specialties")
    expert_prompts = relationship("ExpertPrompt", back_populates="sub_specialty", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("specialty_id", "name", name="_specialty_name_uc"),
    )

class ExpertPrompt(Base):
    __tablename__ = "expert_prompts"

    id = Column(Integer, primary_key=True, index=True)
    sub_specialty_id = Column(Integer, ForeignKey("sub_specialties.id"), nullable=False)
    title = Column(String, index=True, nullable=False)
    template = Column(Text, nullable=False)
    variables_schema = Column(JSON, nullable=False, default={})
    expected_output = Column(Text)
    example_context = Column(Text)
    performance_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sub_specialty = relationship("SubSpecialty", back_populates="expert_prompts")
    expert_associations = relationship("ExpertPromptAssociation", back_populates="expert_prompt", cascade="all, delete-orphan")
    execution_history = relationship("PromptExecutionHistory", back_populates="expert_prompt", cascade="all, delete-orphan")

class Expert(Base):
    __tablename__ = "experts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    prompt_associations = relationship("ExpertPromptAssociation", back_populates="expert", cascade="all, delete-orphan")

class ExpertPromptAssociation(Base):
    __tablename__ = "expert_prompt_associations"

    expert_id = Column(Integer, ForeignKey("experts.id"), primary_key=True)
    prompt_id = Column(Integer, ForeignKey("expert_prompts.id"), primary_key=True)

    expert = relationship("Expert", back_populates="prompt_associations")
    expert_prompt = relationship("ExpertPrompt", back_populates="expert_associations")

class PromptExecutionHistory(Base):
    __tablename__ = "prompt_execution_history"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("expert_prompts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    variables = Column(JSON, nullable=False)
    output = Column(Text)
    llm_provider = Column(String, nullable=False)
    llm_model = Column(String, nullable=False)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    execution_time = Column(Float, default=0.0)
    status = Column(String, nullable=False)  # 'success', 'error', 'pending'
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    expert_prompt = relationship("ExpertPrompt", back_populates="execution_history")
    user = relationship("User", back_populates="execution_history")

class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    api_key_env_var = Column(String, nullable=False)
    base_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    llm_models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")

class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("llm_providers.id"), nullable=False)
    name = Column(String, nullable=False)
    model_identifier = Column(String, nullable=False)
    description = Column(Text)
    max_tokens = Column(Integer)
    cost_per_thousand_tokens_input = Column(Float)
    cost_per_thousand_tokens_output = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provider = relationship("LLMProvider", back_populates="llm_models")

    __table_args__ = (
        UniqueConstraint("provider_id", "model_identifier", name="_provider_model_uc"),
    )

