#!/bin/bash

# ============================================================================
# Rubi Studio MT5 Integration - Test Script
# Version: 3.0.0
# ============================================================================

set -e

API_URL="http://localhost:8000"
API_TOKEN="test-token-12345"

echo "=========================================="
echo "🧪 Rubi Studio MT5 Integration Tests"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour tester un endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_code=$4
    local test_name=$5
    
    echo -n "Testing: $test_name... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_URL$endpoint" \
            -H "Authorization: Bearer $API_TOKEN" \
            -H "Content-Type: application/json")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_URL$endpoint" \
            -H "Authorization: Bearer $API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq "$expected_code" ]; then
        echo -e "${GREEN}✅ PASSED${NC} (HTTP $http_code)"
        echo "   Response: $body" | head -c 100
        echo ""
    else
        echo -e "${RED}❌ FAILED${NC} (Expected $expected_code, got $http_code)"
        echo "   Response: $body"
        echo ""
        return 1
    fi
}

# ============================================================================
# TEST 1: Health Check
# ============================================================================
echo "============================================"
echo "TEST 1: Health Check"
echo "============================================"
test_endpoint "GET" "/health" "" 200 "Health check endpoint"
echo ""

# ============================================================================
# TEST 2: MT5 Connection
# ============================================================================
echo "============================================"
echo "TEST 2: MT5 Connection"
echo "============================================"

# Connexion
connection_data='{
  "account_number": "12345678",
  "broker": "IC Markets",
  "server": "ICMarkets-Demo",
  "balance": 10000.00,
  "equity": 10000.00,
  "currency": "USD"
}'

response=$(curl -s -X POST "$API_URL/api/v1/mt5/connect" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$connection_data")

session_id=$(echo $response | jq -r '.session_id')

if [ "$session_id" != "null" ] && [ -n "$session_id" ]; then
    echo -e "${GREEN}✅ MT5 Connection successful${NC}"
    echo "   Session ID: $session_id"
else
    echo -e "${RED}❌ MT5 Connection failed${NC}"
    echo "   Response: $response"
    exit 1
fi
echo ""

# ============================================================================
# TEST 3: Ping
# ============================================================================
echo "============================================"
echo "TEST 3: Ping"
echo "============================================"

ping_data="{
  \"session_id\": \"$session_id\",
  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
  \"balance\": 10050.00,
  \"equity\": 10070.00,
  \"margin_free\": 9000.00
}"

test_endpoint "POST" "/api/v1/mt5/ping" "$ping_data" 200 "Ping endpoint"
echo ""

# ============================================================================
# TEST 4: Send Trading Signal
# ============================================================================
echo "============================================"
echo "TEST 4: Send Trading Signal"
echo "============================================"

signal_data='{
  "symbol": "EURUSD",
  "signal_type": "BUY",
  "entry_price": 1.1000,
  "stop_loss": 1.0950,
  "take_profit": 1.1100,
  "volume": 0.1,
  "timeframe": "H1",
  "confidence": 0.8,
  "signal_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}'

response=$(curl -s -X POST "$API_URL/api/v1/trading/signals" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$signal_data")

signal_id=$(echo $response | jq -r '.id')

if [ "$signal_id" != "null" ] && [ -n "$signal_id" ]; then
    echo -e "${GREEN}✅ Trading signal sent successfully${NC}"
    echo "   Signal ID: $signal_id"
else
    echo -e "${RED}❌ Failed to send trading signal${NC}"
    echo "   Response: $response"
    exit 1
fi
echo ""

# ============================================================================
# TEST 5: Get Trading Signals
# ============================================================================
echo "============================================"
echo "TEST 5: Get Trading Signals"
echo "============================================"

test_endpoint "GET" "/api/v1/trading/signals?limit=10" "" 200 "Get trading signals"
echo ""

# ============================================================================
# TEST 6: Update Signal Status
# ============================================================================
echo "============================================"
echo "TEST 6: Update Signal Status"
echo "============================================"

status_data="{
  \"signal_id\": $signal_id,
  \"status\": \"EXECUTED\",
  \"message\": \"Order executed successfully. Ticket: 123456789\",
  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
}"

test_endpoint "POST" "/api/v1/trading/signals/$signal_id/status" "$status_data" 200 "Update signal status"
echo ""

# ============================================================================
# TEST 7: Update Positions
# ============================================================================
echo "============================================"
echo "TEST 7: Update Positions"
echo "============================================"

positions_data="{
  \"session_id\": \"$session_id\",
  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
  \"positions\": [
    {
      \"ticket\": \"123456789\",
      \"symbol\": \"EURUSD\",
      \"type\": \"BUY\",
      \"volume\": 0.1,
      \"open_price\": 1.1000,
      \"current_price\": 1.1020,
      \"sl\": 1.0950,
      \"tp\": 1.1100,
      \"profit\": 20.00,
      \"swap\": 0.00,
      \"commission\": -0.70,
      \"open_time\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
    }
  ]
}"

test_endpoint "POST" "/api/v1/trading/positions/update" "$positions_data" 200 "Update positions"
echo ""

# ============================================================================
# TEST 8: Get Positions
# ============================================================================
echo "============================================"
echo "TEST 8: Get Positions"
echo "============================================"

test_endpoint "GET" "/api/v1/trading/positions?session_id=$session_id" "" 200 "Get positions"
echo ""

# ============================================================================
# TEST 9: Update Account Info
# ============================================================================
echo "============================================"
echo "TEST 9: Update Account Info"
echo "============================================"

account_data="{
  \"session_id\": \"$session_id\",
  \"balance\": 10070.00,
  \"equity\": 10090.00,
  \"margin\": 100.00,
  \"margin_free\": 9990.00,
  \"margin_level\": 10090.00,
  \"profit\": 20.00
}"

test_endpoint "POST" "/api/v1/mt5/account/update" "$account_data" 200 "Update account info"
echo ""

# ============================================================================
# TEST 10: Get Account Info
# ============================================================================
echo "============================================"
echo "TEST 10: Get Account Info"
echo "============================================"

test_endpoint "GET" "/api/v1/mt5/account/$session_id" "" 200 "Get account info"
echo ""

# ============================================================================
# TEST 11: Get Statistics
# ============================================================================
echo "============================================"
echo "TEST 11: Get Statistics"
echo "============================================"

test_endpoint "GET" "/api/v1/stats" "" 200 "Get statistics"
echo ""

# ============================================================================
# TEST 12: Get Active Sessions
# ============================================================================
echo "============================================"
echo "TEST 12: Get Active Sessions"
echo "============================================"

test_endpoint "GET" "/api/v1/mt5/sessions" "" 200 "Get active sessions"
echo ""

# ============================================================================
# TEST 13: Disconnect
# ============================================================================
echo "============================================"
echo "TEST 13: Disconnect"
echo "============================================"

disconnect_data="{
  \"session_id\": \"$session_id\",
  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
  \"total_signals_sent\": 10,
  \"total_signals_received\": 5,
  \"total_orders_executed\": 5,
  \"total_errors\": 0
}"

test_endpoint "POST" "/api/v1/mt5/disconnect" "$disconnect_data" 200 "Disconnect session"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "=========================================="
echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - Health check: ✅"
echo "  - MT5 Connection: ✅"
echo "  - Ping: ✅"
echo "  - Send signal: ✅"
echo "  - Get signals: ✅"
echo "  - Update signal status: ✅"
echo "  - Update positions: ✅"
echo "  - Get positions: ✅"
echo "  - Update account info: ✅"
echo "  - Get account info: ✅"
echo "  - Get statistics: ✅"
echo "  - Get active sessions: ✅"
echo "  - Disconnect: ✅"
echo ""
echo "🎉 Rubi Studio MT5 Integration is fully operational!"
echo ""

