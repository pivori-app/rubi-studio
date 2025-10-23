from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import asyncio
import json
import os

# For robust JSON schema validation
from jsonschema import validate, ValidationError

# For LLM abstraction (simplified)
from openai import OpenAI

from . import models, schemas, database

app = FastAPI(title="Rubi Studio Prompt Engineering API")

# Dependency to get the DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=database.engine)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to Rubi Studio Prompt Engineering API"}

# --- LLM Abstraction Layer ---
class LLMService:
    def __init__(self, db: Session):
        self.db = db

    async def call_llm(self, model_id: str, prompt_template: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        llm_model = self.db.query(models.LLMModel).filter(models.LLMModel.model_id == model_id, models.LLMModel.is_active == True).first()
        if not llm_model:
            raise ValueError(f"LLM Model with ID {model_id} not found or is inactive.")

        provider = self.db.query(models.LLMProvider).filter(models.LLMProvider.provider_id == llm_model.provider_id, models.LLMProvider.is_active == True).first()
        if not provider:
            raise ValueError(f"LLM Provider for model {llm_model.name} not found or is inactive.")

        api_key = os.getenv(provider.api_key_env_var)
        if not api_key:
            raise ValueError(f"API key for provider {provider.name} ({provider.api_key_env_var}) not set in environment variables.")

        # Dynamically select LLM client based on provider (simplified for example)
        if "openai" in provider.name.lower():
            client = OpenAI(api_key=api_key)
            # Assuming a simple chat completion for demonstration
            try:
                formatted_prompt = prompt_template.format(**variables)
                response = client.chat.completions.create(
                    model=llm_model.model_identifier,
                    messages=[
                        {"role": "user", "content": formatted_prompt}
                    ]
                )
                generated_text = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
                cost_estimate = (tokens_used / 1000) * (llm_model.cost_per_thousand_tokens_input + llm_model.cost_per_thousand_tokens_output) if llm_model.cost_per_thousand_tokens_input and llm_model.cost_per_thousand_tokens_output else 0

                return {
                    "output": generated_text,
                    "status": "SUCCESS",
                    "metrics": {
                        "tokens_used": tokens_used,
                        "cost_estimate": cost_estimate,
                        "model_name": llm_model.name,
                        "provider_name": provider.name
                    }
                }
            except Exception as e:
                raise ValueError(f"Error calling OpenAI API: {e}")
        elif "gemini" in provider.name.lower():
            # Placeholder for Gemini integration
            await asyncio.sleep(2) # Simulate delay
            formatted_prompt = prompt_template.format(**variables)
            generated_text = f"[Gemini Simulated Response] {formatted_prompt}"
            tokens_used = len(formatted_prompt.split()) * 2
            cost_estimate = (tokens_used / 1000) * (llm_model.cost_per_thousand_tokens_input + llm_model.cost_per_thousand_tokens_output) if llm_model.cost_per_thousand_tokens_input and llm_model.cost_per_thousand_tokens_output else 0
            return {
                "output": generated_text,
                "status": "SUCCESS",
                "metrics": {
                    "tokens_used": tokens_used,
                    "cost_estimate": cost_estimate,
                    "model_name": llm_model.name,
                    "provider_name": provider.name
                }
            }
        else:
            raise ValueError(f"Unsupported LLM Provider: {provider.name}")


# --- Background Task for Prompt Execution ---
async def process_prompt_in_background(execution_id: str, prompt_id: str, variables_data: Dict[str, Any], db_session: Session):
    try:
        # Refresh the execution history entry to update its status
        execution_entry = db_session.query(models.PromptExecutionHistory).filter(models.PromptExecutionHistory.execution_id == execution_id).first()
        if not execution_entry:
            print(f"[Background Task] Execution history entry {execution_id} not found.")
            return

        expert_prompt = db_session.query(models.ExpertPrompt).filter(models.ExpertPrompt.prompt_id == prompt_id).first()
        if expert_prompt is None:
            raise ValueError(f"ExpertPrompt {prompt_id} not found.")

        # Assume a default LLM model for now, or fetch from expert_prompt or user settings
        # For this example, let's assume the ExpertPrompt has a preferred LLMModel ID
        # In a real scenario, this would be more sophisticated.
        # For now, we'll just pick the first active OpenAI model if available
        llm_model = db_session.query(models.LLMModel).join(models.LLMProvider).filter(
            models.LLMModel.is_active == True,
            models.LLMProvider.is_active == True,
            models.LLMProvider.name.ilike('%openai%') # Example: prefer OpenAI
        ).first()

        if not llm_model:
            raise ValueError("No active LLM model found for execution.")

        llm_service = LLMService(db_session)
        llm_response = await llm_service.call_llm(llm_model.model_id, expert_prompt.template, variables_data)

        execution_entry.output_result = llm_response["output"]
        execution_entry.status = llm_response["status"]
        execution_entry.llm_response_metrics = llm_response["metrics"]
        execution_entry.error_message = None
        db_session.commit()

        print(f"[Background Task] Prompt {prompt_id} executed successfully. Execution ID: {execution_id}")

    except Exception as e:
        print(f"[Background Task] Error processing prompt {prompt_id} (Execution ID: {execution_id}): {e}")
        if execution_entry:
            execution_entry.status = "FAILED"
            execution_entry.error_message = str(e)
            db_session.commit()

# --- Endpoints for Specialties ---
@app.post("/specialties/", response_model=schemas.Specialty, tags=["Specialties"])
def create_specialty(specialty: schemas.SpecialtyCreate, db: Session = Depends(get_db)):
    db_specialty = models.Specialty(**specialty.dict())
    db.add(db_specialty)
    db.commit()
    db.refresh(db_specialty)
    return db_specialty

@app.get("/specialties/", response_model=List[schemas.Specialty], tags=["Specialties"])
def read_specialties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    specialties = db.query(models.Specialty).offset(skip).limit(limit).all()
    return specialties

@app.get("/specialties/{specialty_id}", response_model=schemas.Specialty, tags=["Specialties"])
def read_specialty(specialty_id: str, db: Session = Depends(get_db)):
    specialty = db.query(models.Specialty).filter(models.Specialty.specialty_id == specialty_id).first()
    if specialty is None:
        raise HTTPException(status_code=404, detail="Specialty not found")
    return specialty

# --- Endpoints for SubSpecialties ---
@app.post("/sub_specialties/", response_model=schemas.SubSpecialty, tags=["SubSpecialties"])
def create_sub_specialty(sub_specialty: schemas.SubSpecialtyCreate, db: Session = Depends(get_db)):
    db_sub_specialty = models.SubSpecialty(**sub_specialty.dict())
    db.add(db_sub_specialty)
    db.commit()
    db.refresh(db_sub_specialty)
    return db_sub_specialty

@app.get("/sub_specialties/", response_model=List[schemas.SubSpecialty], tags=["SubSpecialties"])
def read_sub_specialties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sub_specialties = db.query(models.SubSpecialty).offset(skip).limit(limit).all()
    return sub_specialties

@app.get("/sub_specialties/{sub_specialty_id}", response_model=schemas.SubSpecialty, tags=["SubSpecialties"])
def read_sub_specialty(sub_specialty_id: str, db: Session = Depends(get_db)):
    sub_specialty = db.query(models.SubSpecialty).filter(models.SubSpecialty.sub_specialty_id == sub_specialty_id).first()
    if sub_specialty is None:
        raise HTTPException(status_code=404, detail="SubSpecialty not found")
    return sub_specialty

@app.get("/specialties/{specialty_id}/sub_specialties/", response_model=List[schemas.SubSpecialty], tags=["SubSpecialties"])
def read_sub_specialties_for_specialty(specialty_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sub_specialties = db.query(models.SubSpecialty).filter(models.SubSpecialty.specialty_id == specialty_id).offset(skip).limit(limit).all()
    return sub_specialties

# --- Endpoints for ExpertPrompts ---
@app.post("/expert_prompts/", response_model=schemas.ExpertPrompt, tags=["Expert Prompts"])
def create_expert_prompt(expert_prompt: schemas.ExpertPromptCreate, db: Session = Depends(get_db)):
    db_expert_prompt = models.ExpertPrompt(**expert_prompt.dict())
    db.add(db_expert_prompt)
    db.commit()
    db.refresh(db_expert_prompt)
    return db_expert_prompt

@app.get("/expert_prompts/", response_model=List[schemas.ExpertPrompt], tags=["Expert Prompts"])
def read_expert_prompts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    expert_prompts = db.query(models.ExpertPrompt).offset(skip).limit(limit).all()
    return expert_prompts

@app.get("/expert_prompts/{prompt_id}", response_model=schemas.ExpertPrompt, tags=["Expert Prompts"])
def read_expert_prompt(prompt_id: str, db: Session = Depends(get_db)):
    expert_prompt = db.query(models.ExpertPrompt).filter(models.ExpertPrompt.prompt_id == prompt_id).first()
    if expert_prompt is None:
        raise HTTPException(status_code=404, detail="ExpertPrompt not found")
    return expert_prompt

@app.get("/sub_specialties/{sub_specialty_id}/expert_prompts/", response_model=List[schemas.ExpertPrompt], tags=["Expert Prompts"])
def read_expert_prompts_for_sub_specialty(sub_specialty_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    expert_prompts = db.query(models.ExpertPrompt).filter(models.ExpertPrompt.sub_specialty_id == sub_specialty_id).offset(skip).limit(limit).all()
    return expert_prompts

# --- Endpoints for Experts ---
@app.post("/experts/", response_model=schemas.Expert, tags=["Experts"])
def create_expert(expert: schemas.ExpertCreate, db: Session = Depends(get_db)):
    db_expert = models.Expert(**expert.dict())
    db.add(db_expert)
    db.commit()
    db.refresh(db_expert)
    return db_expert

@app.get("/experts/", response_model=List[schemas.Expert], tags=["Experts"])
def read_experts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    experts = db.query(models.Expert).offset(skip).limit(limit).all()
    return experts

@app.get("/experts/{expert_id}", response_model=schemas.Expert, tags=["Experts"])
def read_expert(expert_id: str, db: Session = Depends(get_db)):
    expert = db.query(models.Expert).filter(models.Expert.expert_id == expert_id).first()
    if expert is None:
        raise HTTPException(status_code=404, detail="Expert not found")
    return expert

# --- Endpoints for ExpertPromptAssociations ---
@app.post("/expert_prompt_associations/", response_model=schemas.ExpertPromptAssociation, tags=["Expert Prompt Associations"])
def create_expert_prompt_association(association: schemas.ExpertPromptAssociationCreate, db: Session = Depends(get_db)):
    db_association = models.ExpertPromptAssociation(**association.dict())
    db.add(db_association)
    db.commit()
    db.refresh(db_association)
    return db_association

@app.get("/expert_prompt_associations/", response_model=List[schemas.ExpertPromptAssociation], tags=["Expert Prompt Associations"])
def read_expert_prompt_associations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    associations = db.query(models.ExpertPromptAssociation).offset(skip).limit(limit).all()
    return associations

@app.get("/expert_prompt_associations/expert/{expert_id}/prompt/{prompt_id}", response_model=schemas.ExpertPromptAssociation, tags=["Expert Prompt Associations"])
def read_expert_prompt_association(expert_id: str, prompt_id: str, db: Session = Depends(get_db)):
    association = db.query(models.ExpertPromptAssociation).filter(models.ExpertPromptAssociation.expert_id == expert_id, models.ExpertPromptAssociation.prompt_id == prompt_id).first()
    if association is None:
        raise HTTPException(status_code=404, detail="Association not found")
    return association

# --- Endpoints for LLM Providers ---
@app.post("/llm_providers/", response_model=schemas.LLMProvider, tags=["LLM Management"])
def create_llm_provider(llm_provider: schemas.LLMProviderCreate, db: Session = Depends(get_db)):
    db_llm_provider = models.LLMProvider(**llm_provider.dict())
    db.add(db_llm_provider)
    db.commit()
    db.refresh(db_llm_provider)
    return db_llm_provider

@app.get("/llm_providers/", response_model=List[schemas.LLMProvider], tags=["LLM Management"])
def read_llm_providers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    llm_providers = db.query(models.LLMProvider).offset(skip).limit(limit).all()
    return llm_providers

@app.get("/llm_providers/{provider_id}", response_model=schemas.LLMProvider, tags=["LLM Management"])
def read_llm_provider(provider_id: str, db: Session = Depends(get_db)):
    llm_provider = db.query(models.LLMProvider).filter(models.LLMProvider.provider_id == provider_id).first()
    if llm_provider is None:
        raise HTTPException(status_code=404, detail="LLM Provider not found")
    return llm_provider

# --- Endpoints for LLM Models ---
@app.post("/llm_models/", response_model=schemas.LLMModel, tags=["LLM Management"])
def create_llm_model(llm_model: schemas.LLMModelCreate, db: Session = Depends(get_db)):
    db_llm_model = models.LLMModel(**llm_model.dict())
    db.add(db_llm_model)
    db.commit()
    db.refresh(db_llm_model)
    return db_llm_model

@app.get("/llm_models/", response_model=List[schemas.LLMModel], tags=["LLM Management"])
def read_llm_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    llm_models = db.query(models.LLMModel).offset(skip).limit(limit).all()
    return llm_models

@app.get("/llm_models/{model_id}", response_model=schemas.LLMModel, tags=["LLM Management"])
def read_llm_model(model_id: str, db: Session = Depends(get_db)):
    llm_model = db.query(models.LLMModel).filter(models.LLMModel.model_id == model_id).first()
    if llm_model is None:
        raise HTTPException(status_code=404, detail="LLM Model not found")
    return llm_model

# --- Endpoint for executing a prompt ---
@app.post("/execute-prompt/{prompt_id}", response_model=schemas.PromptExecutionResponse, tags=["Prompt Execution"])
async def execute_prompt(prompt_id: str, variables: schemas.PromptExecutionRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    expert_prompt = db.query(models.ExpertPrompt).filter(models.ExpertPrompt.prompt_id == prompt_id).first()
    if expert_prompt is None:
        raise HTTPException(status_code=404, detail="Prompt expert non trouvé")

    # 1. Validate input variables against variables_schema
    if expert_prompt.variables_schema:
        try:
            validate(instance=variables.data, schema=expert_prompt.variables_schema)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Erreur de validation des variables d'entrée: {e.message}")
    elif variables.data: # If schema is empty but data is provided, still allow but warn
        print("Warning: Input variables provided but no variables_schema defined for this prompt.")

    # 2. Create a new execution history entry with PENDING status
    new_execution = models.PromptExecutionHistory(
        prompt_id=prompt_id,
        input_variables=variables.data,
        status="PENDING"
    )
    db.add(new_execution)
    db.commit()
    db.refresh(new_execution)

    # 3. Start background task for LLM call
    background_tasks.add_task(process_prompt_in_background, str(new_execution.execution_id), prompt_id, variables.data, db)

    return {"message": "Prompt execution started in background", "task_id": str(new_execution.execution_id), "execution_id": new_execution.execution_id}

@app.get("/prompt_executions/{execution_id}", response_model=schemas.PromptExecutionHistory, tags=["Prompt Execution"])
def get_prompt_execution_status(execution_id: str, db: Session = Depends(get_db)):
    execution = db.query(models.PromptExecutionHistory).filter(models.PromptExecutionHistory.execution_id == execution_id).first()
    if execution is None:
        raise HTTPException(status_code=404, detail="Historique d'exécution non trouvé")
    return execution

@app.get("/expert_prompts/{prompt_id}/executions", response_model=List[schemas.PromptExecutionHistory], tags=["Prompt Execution"])
def get_prompt_execution_history(prompt_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    history = db.query(models.PromptExecutionHistory).filter(models.PromptExecutionHistory.prompt_id == prompt_id).order_by(models.PromptExecutionHistory.executed_at.desc()).offset(skip).limit(limit).all()
    return history


# --- Versioning (Placeholder - requires more complex logic for actual versioning) ---
# For now, ExpertPrompt is the primary entity. Versioning would involve:
# 1. A 'version' field in ExpertPrompt.
# 2. Logic to create new versions (e.g., duplicating with incremented version number).
# 3. Endpoints to retrieve specific versions.
# This is a significant feature and would require more detailed design and implementation.



