from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

# --- Specialty Schemas ---
class SpecialtyBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None

class SpecialtyCreate(SpecialtyBase):
    pass

class Specialty(SpecialtyBase):
    specialty_id: UUID

    class Config:
        orm_mode = True

# --- SubSpecialty Schemas ---
class SubSpecialtyBase(BaseModel):
    specialty_id: UUID
    name: str
    description: Optional[str] = None

class SubSpecialtyCreate(SubSpecialtyBase):
    pass

class SubSpecialty(SubSpecialtyBase):
    sub_specialty_id: UUID

    class Config:
        orm_mode = True

# --- Expert Schemas ---
class ExpertBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExpertCreate(ExpertBase):
    pass

class Expert(ExpertBase):
    expert_id: UUID

    class Config:
        orm_mode = True

# --- LLMProvider Schemas ---
class LLMProviderBase(BaseModel):
    name: str
    api_key_env_var: str
    base_url: Optional[str] = None
    is_active: bool = True

class LLMProviderCreate(LLMProviderBase):
    pass

class LLMProvider(LLMProviderBase):
    provider_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# --- LLMModel Schemas ---
class LLMModelBase(BaseModel):
    provider_id: UUID
    name: str
    model_identifier: str
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    cost_per_thousand_tokens_input: Optional[float] = None
    cost_per_thousand_tokens_output: Optional[float] = None
    is_active: bool = True

class LLMModelCreate(LLMModelBase):
    pass

class LLMModel(LLMModelBase):
    model_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# --- PromptExecutionHistory Schemas ---
class PromptExecutionHistoryBase(BaseModel):
    prompt_id: UUID
    input_variables: Dict[str, Any]
    output_result: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    llm_response_metrics: Optional[Dict[str, Any]] = None

class PromptExecutionHistoryCreate(PromptExecutionHistoryBase):
    pass

class PromptExecutionHistory(PromptExecutionHistoryBase):
    execution_id: UUID
    executed_at: datetime

    class Config:
        orm_mode = True

# --- ExpertPrompt Schemas (Updated with new relationships) ---
class ExpertPromptBase(BaseModel):
    sub_specialty_id: UUID
    title: str
    template: str
    variables_schema: Dict[str, Any] = Field(default_factory=dict) # JSON field
    expected_output: Optional[str] = None
    example_context: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None # JSON field

class ExpertPromptCreate(ExpertPromptBase):
    pass

class ExpertPrompt(ExpertPromptBase):
    prompt_id: UUID
    created_at: datetime
    updated_at: datetime
    execution_history: List[PromptExecutionHistory] = []

    class Config:
        orm_mode = True

# --- ExpertPromptAssociation Schemas ---
class ExpertPromptAssociationBase(BaseModel):
    expert_id: UUID
    prompt_id: UUID

class ExpertPromptAssociationCreate(ExpertPromptAssociationBase):
    pass

class ExpertPromptAssociation(ExpertPromptAssociationBase):
    class Config:
        orm_mode = True

# --- Request for Prompt Execution ---
class PromptExecutionRequest(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)

# --- Response for Prompt Execution ---
class PromptExecutionResponse(BaseModel):
    message: str
    task_id: str
    execution_id: Optional[UUID] = None





