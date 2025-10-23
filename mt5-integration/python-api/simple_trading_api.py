#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rubi Studio - Simple Trading API
Version: 3.0.0
Purpose: Simple API routes for MT5 trading signals

This module provides simple, easy-to-use API endpoints for traders to send
and receive trading signals from MT5. Perfect for beginners and experienced traders.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import logging

# Setup logging
logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS
# ============================================================================

class SignalType(str, Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    CLOSE_BUY = "CLOSE_BUY"
    CLOSE_SELL = "CLOSE_SELL"

class SignalStatus(str, Enum):
    """Trading signal status."""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class OrderType(str, Enum):
    """Order types."""
    BUY = "BUY"
    SELL = "SELL"

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SimpleTradingSignal(BaseModel):
    """Simple trading signal model for traders."""
    
    symbol: str = Field(..., description="Trading pair (e.g., EURUSD)")
    signal_type: SignalType = Field(..., description="BUY or SELL")
    entry_price: float = Field(..., description="Entry price")
    stop_loss: float = Field(..., description="Stop loss price")
    take_profit: float = Field(..., description="Take profit price")
    volume: float = Field(..., description="Trade volume/lot size")
    timeframe: str = Field(default="H1", description="Timeframe (M5, M15, H1, H4, D1, etc.)")
    confidence: float = Field(default=0.5, ge=0, le=1, description="Signal confidence (0-1)")
    comment: Optional[str] = Field(None, description="Optional comment/strategy name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "EURUSD",
                "signal_type": "BUY",
                "entry_price": 1.1000,
                "stop_loss": 1.0950,
                "take_profit": 1.1100,
                "volume": 0.1,
                "timeframe": "H1",
                "confidence": 0.85,
                "comment": "Breakout strategy"
            }
        }

class SimpleTradeUpdate(BaseModel):
    """Simple trade update model for traders."""
    
    ticket: str = Field(..., description="Order ticket/ID")
    symbol: str = Field(..., description="Trading pair")
    type: OrderType = Field(..., description="BUY or SELL")
    volume: float = Field(..., description="Trade volume")
    open_price: float = Field(..., description="Open price")
    current_price: float = Field(..., description="Current price")
    stop_loss: float = Field(..., description="Stop loss")
    take_profit: float = Field(..., description="Take profit")
    profit: float = Field(..., description="Current profit/loss")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticket": "123456789",
                "symbol": "EURUSD",
                "type": "BUY",
                "volume": 0.1,
                "open_price": 1.1000,
                "current_price": 1.1020,
                "stop_loss": 1.0950,
                "take_profit": 1.1100,
                "profit": 20.00
            }
        }

class SimpleAccountInfo(BaseModel):
    """Simple account info model for traders."""
    
    balance: float = Field(..., description="Account balance")
    equity: float = Field(..., description="Account equity")
    margin: float = Field(..., description="Used margin")
    margin_free: float = Field(..., description="Free margin")
    margin_level: float = Field(..., description="Margin level %")
    profit: float = Field(..., description="Total profit/loss")
    
    class Config:
        json_schema_extra = {
            "example": {
                "balance": 10000.00,
                "equity": 10050.00,
                "margin": 100.00,
                "margin_free": 9950.00,
                "margin_level": 10050.0,
                "profit": 50.00
            }
        }

class SimpleResponse(BaseModel):
    """Simple response model."""
    
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

# ============================================================================
# IN-MEMORY STORAGE (For demo purposes)
# ============================================================================

# In production, use a database
signals_store: Dict[int, Dict[str, Any]] = {}
trades_store: Dict[str, Dict[str, Any]] = {}
account_info_store: Dict[str, Dict[str, Any]] = {
    "default": {
        "balance": 10000.00,
        "equity": 10000.00,
        "margin": 0.00,
        "margin_free": 10000.00,
        "margin_level": 0.0,
        "profit": 0.00
    }
}
signal_counter = 0

# ============================================================================
# API ROUTES
# ============================================================================

router = APIRouter(prefix="/api/v1/simple", tags=["Simple Trading API"])

# ============================================================================
# SIGNAL ENDPOINTS
# ============================================================================

@router.post(
    "/signals",
    response_model=SimpleResponse,
    summary="Send a trading signal",
    description="Send a trading signal from MT5 to the backend"
)
async def send_signal(signal: SimpleTradingSignal = Body(...)):
    """
    Send a trading signal from MT5.
    
    **Example for traders:**
    - When your EA detects a BUY signal on EURUSD, send this request
    - The backend will store the signal and you can retrieve it later
    - Update the status when the order is executed
    
    **Parameters:**
    - symbol: Trading pair (EURUSD, GBPUSD, etc.)
    - signal_type: BUY or SELL
    - entry_price: Where to enter the trade
    - stop_loss: Where to stop if wrong
    - take_profit: Where to take profit
    - volume: Trade size
    - confidence: How confident you are (0-1)
    """
    global signal_counter
    
    try:
        signal_counter += 1
        signal_id = signal_counter
        
        # Store signal
        signals_store[signal_id] = {
            "id": signal_id,
            "symbol": signal.symbol,
            "signal_type": signal.signal_type,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "volume": signal.volume,
            "timeframe": signal.timeframe,
            "confidence": signal.confidence,
            "comment": signal.comment,
            "status": SignalStatus.PENDING,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"Signal #{signal_id} received: {signal.symbol} {signal.signal_type}")
        
        return SimpleResponse(
            success=True,
            message=f"Signal received and stored (ID: {signal_id})",
            data={
                "signal_id": signal_id,
                "symbol": signal.symbol,
                "signal_type": signal.signal_type,
                "status": "PENDING"
            }
        )
    
    except Exception as e:
        logger.error(f"Error sending signal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get(
    "/signals",
    response_model=SimpleResponse,
    summary="Get all trading signals",
    description="Retrieve all trading signals"
)
async def get_signals(
    status: Optional[SignalStatus] = Query(None, description="Filter by status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results")
):
    """
    Get all trading signals.
    
    **Useful for traders to:**
    - See all signals sent
    - Filter by status (PENDING, EXECUTED, etc.)
    - Filter by symbol
    - Monitor signal history
    """
    try:
        signals = list(signals_store.values())
        
        # Filter by status
        if status:
            signals = [s for s in signals if s["status"] == status]
        
        # Filter by symbol
        if symbol:
            signals = [s for s in signals if s["symbol"] == symbol]
        
        # Limit results
        signals = signals[-limit:]
        
        return SimpleResponse(
            success=True,
            message=f"Retrieved {len(signals)} signal(s)",
            data={
                "total": len(signals),
                "signals": signals
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting signals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get(
    "/signals/{signal_id}",
    response_model=SimpleResponse,
    summary="Get a specific signal",
    description="Retrieve details of a specific signal"
)
async def get_signal(signal_id: int):
    """Get details of a specific signal."""
    try:
        if signal_id not in signals_store:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
        
        signal = signals_store[signal_id]
        
        return SimpleResponse(
            success=True,
            message=f"Signal {signal_id} retrieved",
            data=signal
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting signal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post(
    "/signals/{signal_id}/execute",
    response_model=SimpleResponse,
    summary="Mark signal as executed",
    description="Mark a signal as executed when the trade is opened"
)
async def execute_signal(
    signal_id: int,
    ticket: str = Body(..., description="Order ticket from MT5")
):
    """
    Mark a signal as executed.
    
    **When to use:**
    - After your EA opens a trade based on the signal
    - Update the status to EXECUTED
    - Include the order ticket from MT5
    """
    try:
        if signal_id not in signals_store:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
        
        signal = signals_store[signal_id]
        signal["status"] = SignalStatus.EXECUTED
        signal["ticket"] = ticket
        signal["executed_at"] = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"Signal #{signal_id} marked as EXECUTED (Ticket: {ticket})")
        
        return SimpleResponse(
            success=True,
            message=f"Signal {signal_id} marked as executed",
            data={"signal_id": signal_id, "status": "EXECUTED", "ticket": ticket}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing signal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================================================
# TRADE ENDPOINTS
# ============================================================================

@router.post(
    "/trades",
    response_model=SimpleResponse,
    summary="Update trade information",
    description="Update information about an open trade"
)
async def update_trade(trade: SimpleTradeUpdate = Body(...)):
    """
    Update trade information.
    
    **Useful for traders to:**
    - Send current trade details
    - Update profit/loss
    - Monitor open positions
    - Track trade performance
    """
    try:
        ticket = trade.ticket
        
        trades_store[ticket] = {
            "ticket": ticket,
            "symbol": trade.symbol,
            "type": trade.type,
            "volume": trade.volume,
            "open_price": trade.open_price,
            "current_price": trade.current_price,
            "stop_loss": trade.stop_loss,
            "take_profit": trade.take_profit,
            "profit": trade.profit,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"Trade {ticket} updated: P&L ${trade.profit:.2f}")
        
        return SimpleResponse(
            success=True,
            message=f"Trade {ticket} updated",
            data={"ticket": ticket, "profit": trade.profit}
        )
    
    except Exception as e:
        logger.error(f"Error updating trade: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get(
    "/trades",
    response_model=SimpleResponse,
    summary="Get all open trades",
    description="Retrieve all open trades"
)
async def get_trades(symbol: Optional[str] = Query(None, description="Filter by symbol")):
    """
    Get all open trades.
    
    **Useful for traders to:**
    - See all open positions
    - Monitor total profit/loss
    - Filter by symbol
    """
    try:
        trades = list(trades_store.values())
        
        # Filter by symbol
        if symbol:
            trades = [t for t in trades if t["symbol"] == symbol]
        
        # Calculate total profit
        total_profit = sum(t["profit"] for t in trades)
        
        return SimpleResponse(
            success=True,
            message=f"Retrieved {len(trades)} open trade(s)",
            data={
                "total": len(trades),
                "total_profit": total_profit,
                "trades": trades
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get(
    "/trades/{ticket}",
    response_model=SimpleResponse,
    summary="Get a specific trade",
    description="Retrieve details of a specific trade"
)
async def get_trade(ticket: str):
    """Get details of a specific trade."""
    try:
        if ticket not in trades_store:
            raise HTTPException(status_code=404, detail=f"Trade {ticket} not found")
        
        trade = trades_store[ticket]
        
        return SimpleResponse(
            success=True,
            message=f"Trade {ticket} retrieved",
            data=trade
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================================================
# ACCOUNT ENDPOINTS
# ============================================================================

@router.post(
    "/account",
    response_model=SimpleResponse,
    summary="Update account information",
    description="Update account balance, equity, and margin info"
)
async def update_account(account: SimpleAccountInfo = Body(...)):
    """
    Update account information.
    
    **When to use:**
    - Send account info periodically (every minute)
    - Update balance and equity
    - Monitor margin usage
    """
    try:
        account_info_store["default"] = {
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "margin_free": account.margin_free,
            "margin_level": account.margin_level,
            "profit": account.profit,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"Account updated: Balance ${account.balance:.2f}, "
                   f"Equity ${account.equity:.2f}, P&L ${account.profit:.2f}")
        
        return SimpleResponse(
            success=True,
            message="Account information updated",
            data={
                "balance": account.balance,
                "equity": account.equity,
                "profit": account.profit
            }
        )
    
    except Exception as e:
        logger.error(f"Error updating account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get(
    "/account",
    response_model=SimpleResponse,
    summary="Get account information",
    description="Retrieve current account information"
)
async def get_account():
    """
    Get account information.
    
    **Useful for traders to:**
    - Check current balance
    - Monitor equity
    - Check margin usage
    - See total profit/loss
    """
    try:
        account = account_info_store.get("default", {})
        
        return SimpleResponse(
            success=True,
            message="Account information retrieved",
            data=account
        )
    
    except Exception as e:
        logger.error(f"Error getting account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get(
    "/stats",
    response_model=SimpleResponse,
    summary="Get trading statistics",
    description="Get summary statistics about signals and trades"
)
async def get_stats():
    """
    Get trading statistics.
    
    **Useful for traders to:**
    - See total signals sent
    - See executed signals
    - See open trades
    - Monitor trading activity
    """
    try:
        # Calculate statistics
        total_signals = len(signals_store)
        executed_signals = len([s for s in signals_store.values() if s["status"] == SignalStatus.EXECUTED])
        pending_signals = len([s for s in signals_store.values() if s["status"] == SignalStatus.PENDING])
        
        open_trades = len(trades_store)
        total_profit = sum(t["profit"] for t in trades_store.values())
        
        # Win rate
        winning_trades = len([t for t in trades_store.values() if t["profit"] > 0])
        win_rate = (winning_trades / open_trades * 100) if open_trades > 0 else 0
        
        account = account_info_store.get("default", {})
        
        return SimpleResponse(
            success=True,
            message="Statistics retrieved",
            data={
                "signals": {
                    "total": total_signals,
                    "executed": executed_signals,
                    "pending": pending_signals
                },
                "trades": {
                    "open": open_trades,
                    "total_profit": total_profit,
                    "winning": winning_trades,
                    "win_rate": f"{win_rate:.1f}%"
                },
                "account": {
                    "balance": account.get("balance", 0),
                    "equity": account.get("equity", 0),
                    "profit": account.get("profit", 0),
                    "margin_level": account.get("margin_level", 0)
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    response_model=SimpleResponse,
    summary="Health check",
    description="Check if the simple trading API is running"
)
async def health_check():
    """Health check endpoint."""
    return SimpleResponse(
        success=True,
        message="Simple Trading API is running",
        data={
            "version": "3.0.0",
            "signals": len(signals_store),
            "trades": len(trades_store)
        }
    )

