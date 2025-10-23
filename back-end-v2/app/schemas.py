from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Specialty Schemas ---
class SpecialtyBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None

class SpecialtyCreate(SpecialtyBase):
    pass

class SpecialtyResponse(SpecialtyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- SubSpecialty Schemas ---
class SubSpecialtyBase(BaseModel):
    specialty_id: int
    name: str
    description: Optional[str] = None

class SubSpecialtyCreate(SubSpecialtyBase):
    pass

class SubSpecialtyResponse(SubSpecialtyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Expert Schemas ---
class ExpertBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExpertCreate(ExpertBase):
    pass

class ExpertResponse(ExpertBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- ExpertPrompt Schemas ---
class ExpertPromptBase(BaseModel):
    sub_specialty_id: int
    title: str
    template: str
    variables_schema: Dict[str, Any] = Field(default_factory=dict)
    expected_output: Optional[str] = None
    example_context: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class ExpertPromptCreate(ExpertPromptBase):
    pass

class ExpertPromptResponse(ExpertPromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Prompt Execution Schemas ---
class PromptExecutionRequest(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict)
    llm_provider: Optional[str] = "openai"
    llm_model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

class PromptExecutionResponse(BaseModel):
    execution_id: int
    prompt_id: int
    output: str
    llm_provider: str
    llm_model: str
    tokens_used: int
    cost: float
    execution_time: float
    status: str

# --- Execution History Schemas ---
class ExecutionHistoryResponse(BaseModel):
    id: int
    prompt_id: int
    user_id: int
    variables: Dict[str, Any]
    output: Optional[str]
    llm_provider: str
    llm_model: str
    tokens_used: int
    cost: float
    execution_time: float
    status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- LLMProvider Schemas ---
class LLMProviderBase(BaseModel):
    name: str
    api_key_env_var: str
    base_url: Optional[str] = None
    is_active: bool = True

class LLMProviderCreate(LLMProviderBase):
    pass

class LLMProviderResponse(LLMProviderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- LLMModel Schemas ---
class LLMModelBase(BaseModel):
    provider_id: int
    name: str
    model_identifier: str
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    cost_per_thousand_tokens_input: Optional[float] = None
    cost_per_thousand_tokens_output: Optional[float] = None
    is_active: bool = True

class LLMModelCreate(LLMModelBase):
    pass

class LLMModelResponse(LLMModelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

