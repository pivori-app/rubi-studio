"""
Rubi Studio Backend API - Version 2.0
Backend FastAPI amélioré avec corrections critiques
"""

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import time
import hashlib
import json
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response

from . import models, schemas
from .database import SessionLocal, engine
from .llm_providers import LLMFactory, LLMProvider
from .validators import validate_variables_against_schema

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer les tables
models.Base.metadata.create_all(bind=engine)

# Configuration JWT
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuration des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Métriques Prometheus
prompt_executions_total = Counter(
    'prompt_executions_total',
    'Total number of prompt executions',
    ['prompt_id', 'llm_provider', 'status']
)

prompt_execution_duration = Histogram(
    'prompt_execution_duration_seconds',
    'Duration of prompt executions',
    ['prompt_id', 'llm_provider']
)

llm_tokens_used = Counter(
    'llm_tokens_used_total',
    'Total tokens used',
    ['llm_provider', 'model']
)

llm_cost_total = Counter(
    'llm_cost_total_usd',
    'Total cost in USD',
    ['llm_provider', 'model']
)

active_executions = Gauge(
    'active_executions',
    'Number of currently active executions'
)

# Application FastAPI
app = FastAPI(
    title="Rubi Studio API",
    description="API Backend pour la plateforme de Prompt Engineering",
    version="2.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dépendance pour la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fonctions d'authentification
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# Routes d'authentification
@app.post("/api/v1/auth/register", response_model=schemas.UserResponse, tags=["Authentication"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Créer un nouveau compte utilisateur"""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/v1/auth/login", response_model=schemas.Token, tags=["Authentication"])
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    """Se connecter et obtenir un token JWT"""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/auth/me", response_model=schemas.UserResponse, tags=["Authentication"])
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Obtenir les informations de l'utilisateur connecté"""
    return current_user

# Routes pour les Spécialités
@app.get("/api/v1/specialties", response_model=List[schemas.SpecialtyResponse], tags=["Specialties"])
def get_specialties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer la liste des spécialités"""
    specialties = db.query(models.Specialty).offset(skip).limit(limit).all()
    return specialties

@app.post("/api/v1/specialties", response_model=schemas.SpecialtyResponse, tags=["Specialties"])
def create_specialty(
    specialty: schemas.SpecialtyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Créer une nouvelle spécialité"""
    db_specialty = models.Specialty(**specialty.dict())
    db.add(db_specialty)
    db.commit()
    db.refresh(db_specialty)
    return db_specialty

@app.get("/api/v1/specialties/{specialty_id}", response_model=schemas.SpecialtyResponse, tags=["Specialties"])
def get_specialty(specialty_id: int, db: Session = Depends(get_db)):
    """Récupérer une spécialité par ID"""
    specialty = db.query(models.Specialty).filter(models.Specialty.id == specialty_id).first()
    if specialty is None:
        raise HTTPException(status_code=404, detail="Specialty not found")
    return specialty

# Routes pour les Sous-spécialités
@app.get("/api/v1/sub-specialties", response_model=List[schemas.SubSpecialtyResponse], tags=["Sub-Specialties"])
def get_sub_specialties(
    specialty_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des sous-spécialités"""
    query = db.query(models.SubSpecialty)
    if specialty_id:
        query = query.filter(models.SubSpecialty.specialty_id == specialty_id)
    sub_specialties = query.offset(skip).limit(limit).all()
    return sub_specialties

@app.post("/api/v1/sub-specialties", response_model=schemas.SubSpecialtyResponse, tags=["Sub-Specialties"])
def create_sub_specialty(
    sub_specialty: schemas.SubSpecialtyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Créer une nouvelle sous-spécialité"""
    db_sub_specialty = models.SubSpecialty(**sub_specialty.dict())
    db.add(db_sub_specialty)
    db.commit()
    db.refresh(db_sub_specialty)
    return db_sub_specialty

# Routes pour les Prompts Experts
@app.get("/api/v1/expert-prompts", response_model=List[schemas.ExpertPromptResponse], tags=["Expert Prompts"])
def get_expert_prompts(
    sub_specialty_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des prompts experts"""
    query = db.query(models.ExpertPrompt)
    if sub_specialty_id:
        query = query.filter(models.ExpertPrompt.sub_specialty_id == sub_specialty_id)
    prompts = query.offset(skip).limit(limit).all()
    return prompts

@app.get("/api/v1/expert-prompts/{prompt_id}", response_model=schemas.ExpertPromptResponse, tags=["Expert Prompts"])
def get_expert_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """Récupérer un prompt expert par ID"""
    prompt = db.query(models.ExpertPrompt).filter(models.ExpertPrompt.id == prompt_id).first()
    if prompt is None:
        raise HTTPException(status_code=404, detail="Expert prompt not found")
    return prompt

@app.post("/api/v1/expert-prompts", response_model=schemas.ExpertPromptResponse, tags=["Expert Prompts"])
def create_expert_prompt(
    prompt: schemas.ExpertPromptCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Créer un nouveau prompt expert"""
    db_prompt = models.ExpertPrompt(**prompt.dict())
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

# Route d'exécution de prompt (CORRIGÉE)
@app.post("/api/v1/execute-prompt/{prompt_id}", response_model=schemas.PromptExecutionResponse, tags=["Execution"])
async def execute_prompt(
    prompt_id: int,
    execution_request: schemas.PromptExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Exécuter un prompt expert avec les variables fournies
    Cette version implémente l'exécution RÉELLE avec les LLM
    """
    active_executions.inc()
    start_time = time.time()
    
    try:
        # Récupérer le prompt
        prompt = db.query(models.ExpertPrompt).filter(models.ExpertPrompt.id == prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Expert prompt not found")
        
        # Valider les variables contre le schéma
        try:
            validated_variables = validate_variables_against_schema(
                execution_request.variables,
                prompt.variables_schema
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Récupérer le provider LLM (ou utiliser celui par défaut)
        llm_provider_name = execution_request.llm_provider or "openai"
        llm_model_name = execution_request.llm_model or "gpt-4"
        
        # Obtenir le provider LLM
        try:
            llm_provider = LLMFactory.get_provider(llm_provider_name)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Injecter les variables dans le template
        try:
            filled_prompt = prompt.template.format(**validated_variables)
        except KeyError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Missing variable in template: {str(e)}"
            )
        
        # Exécuter le prompt avec le LLM
        logger.info(f"Executing prompt {prompt_id} with {llm_provider_name}/{llm_model_name}")
        
        execution_result = await llm_provider.execute(
            prompt=filled_prompt,
            model=llm_model_name,
            temperature=execution_request.temperature,
            max_tokens=execution_request.max_tokens
        )
        
        # Calculer le coût
        cost = llm_provider.calculate_cost(
            tokens=execution_result["tokens_used"],
            model=llm_model_name
        )
        
        # Enregistrer les métriques
        duration = time.time() - start_time
        
        prompt_executions_total.labels(
            prompt_id=prompt_id,
            llm_provider=llm_provider_name,
            status='success'
        ).inc()
        
        prompt_execution_duration.labels(
            prompt_id=prompt_id,
            llm_provider=llm_provider_name
        ).observe(duration)
        
        llm_tokens_used.labels(
            llm_provider=llm_provider_name,
            model=llm_model_name
        ).inc(execution_result["tokens_used"])
        
        llm_cost_total.labels(
            llm_provider=llm_provider_name,
            model=llm_model_name
        ).inc(cost)
        
        # Enregistrer l'historique d'exécution
        execution_history = models.PromptExecutionHistory(
            prompt_id=prompt_id,
            user_id=current_user.id,
            variables=validated_variables,
            output=execution_result["output"],
            llm_provider=llm_provider_name,
            llm_model=llm_model_name,
            tokens_used=execution_result["tokens_used"],
            cost=cost,
            execution_time=duration,
            status="success"
        )
        db.add(execution_history)
        db.commit()
        db.refresh(execution_history)
        
        return {
            "execution_id": execution_history.id,
            "prompt_id": prompt_id,
            "output": execution_result["output"],
            "llm_provider": llm_provider_name,
            "llm_model": llm_model_name,
            "tokens_used": execution_result["tokens_used"],
            "cost": cost,
            "execution_time": duration,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing prompt {prompt_id}: {str(e)}")
        
        prompt_executions_total.labels(
            prompt_id=prompt_id,
            llm_provider=execution_request.llm_provider or "unknown",
            status='error'
        ).inc()
        
        # Enregistrer l'échec dans l'historique
        execution_history = models.PromptExecutionHistory(
            prompt_id=prompt_id,
            user_id=current_user.id,
            variables=execution_request.variables,
            output=None,
            llm_provider=execution_request.llm_provider or "unknown",
            llm_model=execution_request.llm_model or "unknown",
            tokens_used=0,
            cost=0.0,
            execution_time=time.time() - start_time,
            status="error",
            error_message=str(e)
        )
        db.add(execution_history)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
    
    finally:
        active_executions.dec()

# Routes pour l'historique d'exécution
@app.get("/api/v1/executions/history", response_model=List[schemas.ExecutionHistoryResponse], tags=["Execution"])
def get_execution_history(
    skip: int = 0,
    limit: int = 100,
    prompt_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Récupérer l'historique des exécutions de prompts"""
    query = db.query(models.PromptExecutionHistory).filter(
        models.PromptExecutionHistory.user_id == current_user.id
    )
    
    if prompt_id:
        query = query.filter(models.PromptExecutionHistory.prompt_id == prompt_id)
    if status:
        query = query.filter(models.PromptExecutionHistory.status == status)
    
    executions = query.order_by(models.PromptExecutionHistory.created_at.desc()).offset(skip).limit(limit).all()
    return executions

@app.get("/api/v1/executions/{execution_id}", response_model=schemas.ExecutionHistoryResponse, tags=["Execution"])
def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Récupérer une exécution spécifique par ID"""
    execution = db.query(models.PromptExecutionHistory).filter(
        models.PromptExecutionHistory.id == execution_id,
        models.PromptExecutionHistory.user_id == current_user.id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution

# Route pour les métriques Prometheus
@app.get("/metrics", tags=["Monitoring"])
def metrics():
    """Endpoint pour les métriques Prometheus"""
    return Response(content=generate_latest(), media_type="text/plain")

# Route de santé
@app.get("/health", tags=["Health"])
def health_check():
    """Vérifier l'état de santé de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

# Route racine
@app.get("/", tags=["Root"])
def read_root():
    """Point d'entrée de l'API"""
    return {
        "message": "Bienvenue sur l'API Rubi Studio",
        "version": "2.0.0",
        "documentation": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

