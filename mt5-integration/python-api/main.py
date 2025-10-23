"""
Rubi Studio - MT5 Trading API
FastAPI backend pour recevoir et gérer les signaux de trading MT5
Version: 3.0.0
"""

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
import logging
import uuid
import json
from enum import Enum
from simple_trading_api import router as simple_router

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# MODELS & SCHEMAS
# ============================================================================

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    CLOSE_BUY = "CLOSE_BUY"
    CLOSE_SELL = "CLOSE_SELL"

class SignalStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class MT5ConnectionRequest(BaseModel):
    """Requête de connexion MT5"""
    account_number: str
    broker: str
    server: Optional[str] = None
    balance: float
    equity: float
    currency: str = "USD"

class MT5ConnectionResponse(BaseModel):
    """Réponse de connexion MT5"""
    session_id: str
    message: str
    connected_at: datetime

class MT5PingRequest(BaseModel):
    """Requête de ping"""
    session_id: str
    timestamp: str
    balance: float
    equity: float
    margin_free: float

class TradingSignalCreate(BaseModel):
    """Signal de trading entrant depuis MT5"""
    symbol: str = Field(..., description="Symbole tradé (ex: EURUSD)")
    signal_type: SignalType
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    volume: float = Field(..., gt=0, description="Taille du lot")
    timeframe: Optional[str] = "H1"
    confidence: Optional[float] = Field(default=0.5, ge=0, le=1)
    indicators: Optional[Dict[str, Any]] = {}
    signal_time: datetime
    strategy_id: Optional[int] = None
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()
    
    @validator('volume')
    def validate_volume(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Volume must be between 0 and 100 lots')
        return v

class TradingSignalResponse(BaseModel):
    """Réponse signal de trading"""
    id: int
    user_id: int
    symbol: str
    signal_type: SignalType
    status: SignalStatus
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    volume: float
    timeframe: Optional[str]
    confidence: Optional[float]
    signal_time: datetime
    received_at: datetime
    executed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class PositionUpdate(BaseModel):
    """Mise à jour de position depuis MT5"""
    ticket: str
    symbol: str
    type: str  # BUY or SELL
    volume: float
    open_price: float
    current_price: float
    sl: float
    tp: float
    profit: float
    swap: float
    commission: float
    open_time: str

class PositionsUpdateRequest(BaseModel):
    """Requête de mise à jour des positions"""
    session_id: str
    timestamp: str
    positions: List[PositionUpdate]

class SignalStatusUpdate(BaseModel):
    """Mise à jour du statut d'un signal"""
    signal_id: int
    status: SignalStatus
    message: str
    timestamp: str

class AccountInfoUpdate(BaseModel):
    """Mise à jour des informations du compte"""
    session_id: str
    balance: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    profit: float

class MT5DisconnectRequest(BaseModel):
    """Requête de déconnexion"""
    session_id: str
    timestamp: str
    total_signals_sent: int
    total_signals_received: int
    total_orders_executed: int
    total_errors: int

# ============================================================================
# IN-MEMORY STORAGE (À remplacer par PostgreSQL en production)
# ============================================================================

# Sessions MT5 actives
mt5_sessions: Dict[str, Dict[str, Any]] = {}

# Signaux de trading
trading_signals: List[Dict[str, Any]] = []

# Positions ouvertes
open_positions: Dict[str, List[Dict[str, Any]]] = {}

# Informations des comptes
account_info: Dict[str, Dict[str, Any]] = {}

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Rubi Studio MT5 Trading API",
    description="API Backend pour recevoir et gérer les signaux de trading MT5",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sécurité
security = HTTPBearer()

# ============================================================================
# AUTHENTICATION
# ============================================================================

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Vérifier le token API"""
    token = credentials.credentials
    
    # TODO: Implémenter la vérification réelle du token avec JWT
    # Pour le moment, accepter tous les tokens non vides
    if not token or len(token) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token

# ============================================================================
# MT5 CONNECTION ROUTES
# ============================================================================

@app.post("/api/v1/mt5/connect", response_model=MT5ConnectionResponse, tags=["MT5 Connection"])
async def connect_mt5(
    connection: MT5ConnectionRequest,
    token: str = Depends(verify_token)
):
    """
    Établir une connexion avec MT5
    
    **Workflow:**
    1. Générer un session_id unique
    2. Enregistrer la session
    3. Retourner le session_id au client MT5
    """
    session_id = str(uuid.uuid4())
    
    mt5_sessions[session_id] = {
        "session_id": session_id,
        "account_number": connection.account_number,
        "broker": connection.broker,
        "server": connection.server,
        "balance": connection.balance,
        "equity": connection.equity,
        "currency": connection.currency,
        "connected_at": datetime.utcnow(),
        "last_ping": datetime.utcnow(),
        "is_active": True
    }
    
    logger.info(f"MT5 connected: Account {connection.account_number} @ {connection.broker}")
    
    return MT5ConnectionResponse(
        session_id=session_id,
        message="Connected successfully",
        connected_at=datetime.utcnow()
    )

@app.post("/api/v1/mt5/ping", tags=["MT5 Connection"])
async def ping_mt5(
    ping: MT5PingRequest,
    token: str = Depends(verify_token)
):
    """
    Ping pour maintenir la connexion active
    """
    if ping.session_id not in mt5_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Mettre à jour le dernier ping
    mt5_sessions[ping.session_id]["last_ping"] = datetime.utcnow()
    mt5_sessions[ping.session_id]["balance"] = ping.balance
    mt5_sessions[ping.session_id]["equity"] = ping.equity
    mt5_sessions[ping.session_id]["margin_free"] = ping.margin_free
    
    return {"status": "ok", "message": "Ping received"}

@app.post("/api/v1/mt5/disconnect", tags=["MT5 Connection"])
async def disconnect_mt5(
    disconnect: MT5DisconnectRequest,
    token: str = Depends(verify_token)
):
    """
    Déconnecter une session MT5
    """
    if disconnect.session_id in mt5_sessions:
        session = mt5_sessions[disconnect.session_id]
        session["is_active"] = False
        session["disconnected_at"] = datetime.utcnow()
        session["statistics"] = {
            "total_signals_sent": disconnect.total_signals_sent,
            "total_signals_received": disconnect.total_signals_received,
            "total_orders_executed": disconnect.total_orders_executed,
            "total_errors": disconnect.total_errors
        }
        
        logger.info(f"MT5 disconnected: Session {disconnect.session_id}")
        logger.info(f"Statistics: {session['statistics']}")
    
    return {"status": "ok", "message": "Disconnected successfully"}

@app.get("/api/v1/mt5/sessions", tags=["MT5 Connection"])
async def get_active_sessions(token: str = Depends(verify_token)):
    """
    Récupérer toutes les sessions actives
    """
    active_sessions = [
        session for session in mt5_sessions.values()
        if session.get("is_active", False)
    ]
    
    return {
        "total": len(active_sessions),
        "sessions": active_sessions
    }

# ============================================================================
# TRADING SIGNALS ROUTES
# ============================================================================

@app.post("/api/v1/trading/signals", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED, tags=["Trading Signals"])
async def receive_trading_signal(
    signal: TradingSignalCreate,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """
    Recevoir un signal de trading depuis MT5
    
    **Workflow:**
    1. Valider le signal
    2. Enregistrer en mémoire (ou base de données)
    3. Déclencher l'exécution en arrière-plan
    4. Retourner une confirmation
    """
    signal_id = len(trading_signals) + 1
    
    signal_data = {
        "id": signal_id,
        "user_id": 1,  # TODO: Récupérer depuis le token
        "symbol": signal.symbol,
        "signal_type": signal.signal_type.value,
        "status": SignalStatus.PENDING.value,
        "entry_price": signal.entry_price,
        "stop_loss": signal.stop_loss,
        "take_profit": signal.take_profit,
        "volume": signal.volume,
        "timeframe": signal.timeframe,
        "confidence": signal.confidence,
        "indicators": signal.indicators,
        "signal_time": signal.signal_time,
        "received_at": datetime.utcnow(),
        "executed_at": None
    }
    
    trading_signals.append(signal_data)
    
    logger.info(f"Signal received: {signal.symbol} {signal.signal_type.value} {signal.volume} lots")
    
    # Déclencher l'exécution en arrière-plan
    background_tasks.add_task(process_signal, signal_id)
    
    return {
        "id": signal_id,
        "status": "received",
        "message": "Signal received and queued for processing"
    }

@app.get("/api/v1/trading/signals", tags=["Trading Signals"])
async def get_trading_signals(
    symbol: Optional[str] = None,
    status: Optional[SignalStatus] = None,
    limit: int = 100,
    token: str = Depends(verify_token)
):
    """
    Récupérer les signaux de trading
    """
    filtered_signals = trading_signals.copy()
    
    if symbol:
        filtered_signals = [s for s in filtered_signals if s["symbol"] == symbol.upper()]
    
    if status:
        filtered_signals = [s for s in filtered_signals if s["status"] == status.value]
    
    # Limiter le nombre de résultats
    filtered_signals = filtered_signals[-limit:]
    
    return {
        "total": len(filtered_signals),
        "signals": filtered_signals
    }

@app.get("/api/v1/trading/signals/pending", tags=["Trading Signals"])
async def get_pending_signals(
    session_id: str,
    token: str = Depends(verify_token)
):
    """
    Récupérer les signaux en attente pour une session MT5
    
    Utilisé par MT5 pour récupérer les signaux à exécuter
    """
    pending_signals = [
        s for s in trading_signals
        if s["status"] == SignalStatus.PENDING.value
    ]
    
    return {
        "total": len(pending_signals),
        "signals": pending_signals
    }

@app.post("/api/v1/trading/signals/{signal_id}/status", tags=["Trading Signals"])
async def update_signal_status(
    signal_id: int,
    status_update: SignalStatusUpdate,
    token: str = Depends(verify_token)
):
    """
    Mettre à jour le statut d'un signal
    
    Appelé par MT5 après l'exécution d'un signal
    """
    # Trouver le signal
    signal = next((s for s in trading_signals if s["id"] == signal_id), None)
    
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    # Mettre à jour le statut
    signal["status"] = status_update.status.value
    signal["status_message"] = status_update.message
    
    if status_update.status == SignalStatus.EXECUTED:
        signal["executed_at"] = datetime.utcnow()
    
    logger.info(f"Signal {signal_id} status updated: {status_update.status.value}")
    
    return {
        "status": "ok",
        "message": "Signal status updated"
    }

# ============================================================================
# POSITIONS ROUTES
# ============================================================================

@app.post("/api/v1/trading/positions/update", tags=["Positions"])
async def update_positions(
    positions_update: PositionsUpdateRequest,
    token: str = Depends(verify_token)
):
    """
    Mettre à jour les positions ouvertes depuis MT5
    """
    session_id = positions_update.session_id
    
    if session_id not in mt5_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Stocker les positions
    open_positions[session_id] = [pos.dict() for pos in positions_update.positions]
    
    logger.info(f"Positions updated for session {session_id}: {len(positions_update.positions)} positions")
    
    return {
        "status": "ok",
        "message": f"{len(positions_update.positions)} positions updated"
    }

@app.get("/api/v1/trading/positions", tags=["Positions"])
async def get_positions(
    session_id: Optional[str] = None,
    token: str = Depends(verify_token)
):
    """
    Récupérer les positions ouvertes
    """
    if session_id:
        positions = open_positions.get(session_id, [])
        return {
            "session_id": session_id,
            "total": len(positions),
            "positions": positions
        }
    else:
        # Retourner toutes les positions
        all_positions = []
        for sid, positions in open_positions.items():
            all_positions.extend(positions)
        
        return {
            "total": len(all_positions),
            "positions": all_positions
        }

# ============================================================================
# ACCOUNT INFO ROUTES
# ============================================================================

@app.post("/api/v1/mt5/account/update", tags=["Account"])
async def update_account_info(
    account_update: AccountInfoUpdate,
    token: str = Depends(verify_token)
):
    """
    Mettre à jour les informations du compte
    """
    session_id = account_update.session_id
    
    if session_id not in mt5_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    account_info[session_id] = {
        "balance": account_update.balance,
        "equity": account_update.equity,
        "margin": account_update.margin,
        "margin_free": account_update.margin_free,
        "margin_level": account_update.margin_level,
        "profit": account_update.profit,
        "updated_at": datetime.utcnow()
    }
    
    return {
        "status": "ok",
        "message": "Account info updated"
    }

@app.get("/api/v1/mt5/account/{session_id}", tags=["Account"])
async def get_account_info(
    session_id: str,
    token: str = Depends(verify_token)
):
    """
    Récupérer les informations du compte
    """
    if session_id not in mt5_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = mt5_sessions[session_id]
    account = account_info.get(session_id, {})
    
    return {
        "session_id": session_id,
        "account_number": session["account_number"],
        "broker": session["broker"],
        "balance": account.get("balance", session.get("balance", 0)),
        "equity": account.get("equity", session.get("equity", 0)),
        "margin": account.get("margin", 0),
        "margin_free": account.get("margin_free", 0),
        "margin_level": account.get("margin_level", 0),
        "profit": account.get("profit", 0),
        "updated_at": account.get("updated_at")
    }

# ============================================================================
# STATISTICS & MONITORING
# ============================================================================

@app.get("/api/v1/stats", tags=["Statistics"])
async def get_statistics(token: str = Depends(verify_token)):
    """
    Récupérer les statistiques globales
    """
    total_signals = len(trading_signals)
    executed_signals = len([s for s in trading_signals if s["status"] == SignalStatus.EXECUTED.value])
    pending_signals = len([s for s in trading_signals if s["status"] == SignalStatus.PENDING.value])
    rejected_signals = len([s for s in trading_signals if s["status"] == SignalStatus.REJECTED.value])
    
    active_sessions = len([s for s in mt5_sessions.values() if s.get("is_active", False)])
    
    total_positions = sum(len(positions) for positions in open_positions.values())
    
    return {
        "signals": {
            "total": total_signals,
            "executed": executed_signals,
            "pending": pending_signals,
            "rejected": rejected_signals
        },
        "sessions": {
            "active": active_sessions,
            "total": len(mt5_sessions)
        },
        "positions": {
            "open": total_positions
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0"
    }

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def process_signal(signal_id: int):
    """
    Traiter un signal en arrière-plan
    
    TODO: Implémenter la logique de traitement
    - Validation du signal
    - Vérification des risques
    - Envoi à MT5 pour exécution
    """
    logger.info(f"Processing signal {signal_id}...")
    
    # Simuler un traitement
    import asyncio
    await asyncio.sleep(1)
    
    logger.info(f"Signal {signal_id} processed")

# ============================================================================
# WEBSOCKET (pour communication temps réel)
# ============================================================================

@app.websocket("/ws/trading/live/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket pour les mises à jour en temps réel
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {session_id}")
    
    try:
        while True:
            # Recevoir des messages du client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Traiter le message
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            
            # TODO: Envoyer les mises à jour de positions, signaux, etc.
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

app.include_router(simple_router)

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Événement de démarrage
    """
    logger.info("🚀 Rubi Studio MT5 Trading API started")
    logger.info("📡 Listening for MT5 signals...")
    logger.info("✅ Simple Trading API routes loaded")
    logger.info("📚 Documentation available at /docs")
    logger.info("🧪 Test script available at test_mt5_connection.py")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Événement d'arrêt
    """
    logger.info("🛑 Rubi Studio MT5 Trading API stopped")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

