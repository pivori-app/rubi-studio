from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint, Boolean, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
from datetime import datetime

Base = declarative_base()

class Specialty(Base):
    __tablename__ = "specialties"

    specialty_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    icon_url = Column(String)

    sub_specialties = relationship("SubSpecialty", back_populates="specialty", cascade="all, delete-orphan")

class SubSpecialty(Base):
    __tablename__ = "sub_specialties"

    sub_specialty_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specialty_id = Column(UUID(as_uuid=True), ForeignKey("specialties.specialty_id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)

    specialty = relationship("Specialty", back_populates="sub_specialties")
    expert_prompts = relationship("ExpertPrompt", back_populates="sub_specialty", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("specialty_id", "name", name="_specialty_name_uc"),
    )

class ExpertPrompt(Base):
    __tablename__ = "expert_prompts"

    prompt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sub_specialty_id = Column(UUID(as_uuid=True), ForeignKey("sub_specialties.sub_specialty_id"), nullable=False)
    title = Column(String, index=True, nullable=False)
    template = Column(Text, nullable=False)
    variables_schema = Column(JSON, nullable=False, default={})
    expected_output = Column(Text)
    example_context = Column(Text)
    performance_metrics = Column(JSON) # To store aggregated metrics or configuration for metrics
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    sub_specialty = relationship("SubSpecialty", back_populates="expert_prompts")
    expert_associations = relationship("ExpertPromptAssociation", back_populates="expert_prompt", cascade="all, delete-orphan")
    execution_history = relationship("PromptExecutionHistory", back_populates="expert_prompt", cascade="all, delete-orphan")

class Expert(Base):
    __tablename__ = "experts"

    expert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)

    prompt_associations = relationship("ExpertPromptAssociation", back_populates="expert", cascade="all, delete-orphan")

class ExpertPromptAssociation(Base):
    __tablename__ = "expert_prompt_associations"

    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), primary_key=True)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("expert_prompts.prompt_id"), primary_key=True)

    expert = relationship("Expert", back_populates="prompt_associations")
    expert_prompt = relationship("ExpertPrompt", back_populates="expert_associations")

class PromptExecutionHistory(Base):
    __tablename__ = "prompt_execution_history"

    execution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("expert_prompts.prompt_id"), nullable=False)
    executed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    input_variables = Column(JSON, nullable=False)
    output_result = Column(Text)
    status = Column(String, nullable=False) # e.g., 'SUCCESS', 'FAILED', 'PENDING'
    error_message = Column(Text)
    llm_response_metrics = Column(JSON) # e.g., tokens used, cost, model name

    expert_prompt = relationship("ExpertPrompt", back_populates="execution_history")

class LLMProvider(Base):
    __tablename__ = "llm_providers"

    provider_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    api_key_env_var = Column(String, nullable=False) # Environment variable name for API key
    base_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    llm_models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")

class LLMModel(Base):
    __tablename__ = "llm_models"

    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("llm_providers.provider_id"), nullable=False)
    name = Column(String, nullable=False) # e.g., "gemini-pro", "gpt-4"
    model_identifier = Column(String, nullable=False) # Actual identifier used in API calls
    description = Column(Text)
    max_tokens = Column(Integer)
    cost_per_thousand_tokens_input = Column(Float)
    cost_per_thousand_tokens_output = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    provider = relationship("LLMProvider", back_populates="llm_models")

    __table_args__ = (
        UniqueConstraint("provider_id", "model_identifier", name="_provider_model_uc"),
    )


