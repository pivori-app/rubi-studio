#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rubi Studio - MT5 Connection Test Script
Version: 3.0.0
Purpose: Simple test to verify MT5 ↔ Backend connection

This script simulates MT5 sending signals to the backend and verifies the connection.
Perfect for traders to test their setup before going live.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import sys

# Configuration
API_BASE_URL = "http://localhost:8000"
API_TOKEN = "test-token-12345"
TIMEOUT = 10

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def make_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
    """
    Make an HTTP request to the backend API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (e.g., "/api/v1/mt5/connect")
        data: JSON data to send (for POST requests)
    
    Returns:
        Response JSON or None if request fails
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT)
        else:
            print_error(f"Unsupported HTTP method: {method}")
            return None
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return None
    
    except requests.exceptions.ConnectionError:
        print_error(f"Connection refused. Is the backend running on {API_BASE_URL}?")
        return None
    except requests.exceptions.Timeout:
        print_error(f"Request timeout (>{TIMEOUT}s). Backend may be slow.")
        return None
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return None

def test_health_check() -> bool:
    """Test 1: Health check."""
    print_info("Testing backend health...")
    
    response = make_request("GET", "/health")
    if response and response.get("status") == "healthy":
        print_success(f"Backend is healthy (v{response.get('version', 'unknown')})")
        return True
    else:
        print_error("Backend health check failed")
        return False

def test_mt5_connection() -> Optional[str]:
    """Test 2: MT5 Connection."""
    print_info("Connecting to backend as MT5 terminal...")
    
    connection_data = {
        "account_number": "12345678",
        "broker": "IC Markets",
        "server": "ICMarkets-Demo",
        "balance": 10000.00,
        "equity": 10000.00,
        "currency": "USD"
    }
    
    response = make_request("POST", "/api/v1/mt5/connect", connection_data)
    if response and "session_id" in response:
        session_id = response["session_id"]
        print_success(f"Connected successfully! Session ID: {session_id}")
        return session_id
    else:
        print_error("Failed to connect to backend")
        return None

def test_ping(session_id: str) -> bool:
    """Test 3: Ping to keep connection alive."""
    print_info("Sending ping to keep connection alive...")
    
    ping_data = {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "balance": 10050.00,
        "equity": 10070.00,
        "margin_free": 9000.00
    }
    
    response = make_request("POST", "/api/v1/mt5/ping", ping_data)
    if response and response.get("status") == "ok":
        print_success("Ping successful - connection is alive")
        return True
    else:
        print_error("Ping failed")
        return False

def test_send_signal(session_id: str) -> Optional[int]:
    """Test 4: Send a trading signal."""
    print_info("Sending a trading signal (BUY EURUSD)...")
    
    signal_data = {
        "symbol": "EURUSD",
        "signal_type": "BUY",
        "entry_price": 1.1000,
        "stop_loss": 1.0950,
        "take_profit": 1.1100,
        "volume": 0.1,
        "timeframe": "H1",
        "confidence": 0.85,
        "signal_time": datetime.utcnow().isoformat() + "Z"
    }
    
    response = make_request("POST", "/api/v1/trading/signals", signal_data)
    if response and "id" in response:
        signal_id = response["id"]
        print_success(f"Signal sent successfully! Signal ID: {signal_id}")
        print_info(f"  Symbol: {response.get('symbol')}")
        print_info(f"  Type: {response.get('signal_type')}")
        print_info(f"  Status: {response.get('status')}")
        return signal_id
    else:
        print_error("Failed to send signal")
        return None

def test_get_signals() -> bool:
    """Test 5: Get all trading signals."""
    print_info("Retrieving all trading signals...")
    
    response = make_request("GET", "/api/v1/trading/signals?limit=10")
    if response and "signals" in response:
        total = response.get("total", 0)
        print_success(f"Retrieved {total} signal(s)")
        
        for signal in response.get("signals", [])[:3]:  # Show first 3
            print_info(f"  - {signal.get('symbol')} {signal.get('signal_type')} "
                      f"(Status: {signal.get('status')})")
        
        return True
    else:
        print_error("Failed to retrieve signals")
        return False

def test_update_position(session_id: str) -> bool:
    """Test 6: Update trading positions."""
    print_info("Updating trading positions...")
    
    positions_data = {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "positions": [
            {
                "ticket": "123456789",
                "symbol": "EURUSD",
                "type": "BUY",
                "volume": 0.1,
                "open_price": 1.1000,
                "current_price": 1.1020,
                "sl": 1.0950,
                "tp": 1.1100,
                "profit": 20.00,
                "swap": 0.00,
                "commission": -0.70,
                "open_time": datetime.utcnow().isoformat() + "Z"
            }
        ]
    }
    
    response = make_request("POST", "/api/v1/trading/positions/update", positions_data)
    if response and response.get("status") == "ok":
        print_success(f"Position updated: {response.get('message')}")
        return True
    else:
        print_error("Failed to update position")
        return False

def test_get_positions(session_id: str) -> bool:
    """Test 7: Get current positions."""
    print_info("Retrieving current positions...")
    
    response = make_request("GET", f"/api/v1/trading/positions?session_id={session_id}")
    if response and "positions" in response:
        total = response.get("total", 0)
        print_success(f"Retrieved {total} open position(s)")
        
        for pos in response.get("positions", []):
            profit = pos.get("profit", 0)
            profit_color = Colors.OKGREEN if profit >= 0 else Colors.FAIL
            print_info(f"  - {pos.get('symbol')} {pos.get('type')} "
                      f"Vol: {pos.get('volume')} "
                      f"{profit_color}P&L: ${profit:.2f}{Colors.ENDC}")
        
        return True
    else:
        print_error("Failed to retrieve positions")
        return False

def test_get_statistics() -> bool:
    """Test 8: Get statistics."""
    print_info("Retrieving statistics...")
    
    response = make_request("GET", "/api/v1/stats")
    if response and "signals" in response:
        signals = response.get("signals", {})
        sessions = response.get("sessions", {})
        
        print_success("Statistics retrieved:")
        print_info(f"  Signals - Total: {signals.get('total')}, "
                  f"Executed: {signals.get('executed')}, "
                  f"Pending: {signals.get('pending')}")
        print_info(f"  Sessions - Active: {sessions.get('active')}, "
                  f"Total: {sessions.get('total')}")
        
        return True
    else:
        print_error("Failed to retrieve statistics")
        return False

def test_disconnect(session_id: str) -> bool:
    """Test 9: Disconnect session."""
    print_info("Disconnecting from backend...")
    
    disconnect_data = {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_signals_sent": 1,
        "total_signals_received": 1,
        "total_orders_executed": 1,
        "total_errors": 0
    }
    
    response = make_request("POST", "/api/v1/mt5/disconnect", disconnect_data)
    if response and response.get("status") == "ok":
        print_success("Disconnected successfully")
        return True
    else:
        print_error("Failed to disconnect")
        return False

def main():
    """Main test function."""
    print_header("🤖 Rubi Studio - MT5 Connection Test")
    
    print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
    print(f"  Backend URL: {API_BASE_URL}")
    print(f"  API Token: {API_TOKEN}")
    print(f"  Timeout: {TIMEOUT}s\n")
    
    # Test counter
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Health Check
    print_header("Test 1/9: Health Check")
    tests_total += 1
    if test_health_check():
        tests_passed += 1
    
    # Test 2: MT5 Connection
    print_header("Test 2/9: MT5 Connection")
    tests_total += 1
    session_id = test_mt5_connection()
    if session_id:
        tests_passed += 1
        time.sleep(1)  # Small delay between requests
    else:
        print_error("Cannot continue without session ID")
        sys.exit(1)
    
    # Test 3: Ping
    print_header("Test 3/9: Ping")
    tests_total += 1
    if test_ping(session_id):
        tests_passed += 1
    time.sleep(1)
    
    # Test 4: Send Signal
    print_header("Test 4/9: Send Trading Signal")
    tests_total += 1
    signal_id = test_send_signal(session_id)
    if signal_id:
        tests_passed += 1
    time.sleep(1)
    
    # Test 5: Get Signals
    print_header("Test 5/9: Get Trading Signals")
    tests_total += 1
    if test_get_signals():
        tests_passed += 1
    time.sleep(1)
    
    # Test 6: Update Position
    print_header("Test 6/9: Update Position")
    tests_total += 1
    if test_update_position(session_id):
        tests_passed += 1
    time.sleep(1)
    
    # Test 7: Get Positions
    print_header("Test 7/9: Get Positions")
    tests_total += 1
    if test_get_positions(session_id):
        tests_passed += 1
    time.sleep(1)
    
    # Test 8: Statistics
    print_header("Test 8/9: Get Statistics")
    tests_total += 1
    if test_get_statistics():
        tests_passed += 1
    time.sleep(1)
    
    # Test 9: Disconnect
    print_header("Test 9/9: Disconnect")
    tests_total += 1
    if test_disconnect(session_id):
        tests_passed += 1
    
    # Final Summary
    print_header("📊 Test Summary")
    
    success_rate = (tests_passed / tests_total) * 100
    
    if success_rate == 100:
        print_success(f"All tests passed! ({tests_passed}/{tests_total})")
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ MT5 ↔ Backend connection is working perfectly!{Colors.ENDC}\n")
        return 0
    elif success_rate >= 80:
        print_warning(f"Most tests passed ({tests_passed}/{tests_total})")
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  Some issues detected. Check the logs above.{Colors.ENDC}\n")
        return 1
    else:
        print_error(f"Many tests failed ({tests_passed}/{tests_total})")
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ MT5 ↔ Backend connection has issues.{Colors.ENDC}\n")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

