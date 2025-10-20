#!/bin/bash

# Mock Trading Bot Test Script
# Tests the trading bot with mock position creation

# Set the base URL (change this if your service is running elsewhere)
# For production: http://api.alphintra.com/api/trading
# For local: http://localhost:8008/api/trading
BASE_URL="${TRADING_ENGINE_URL:-http://api.alphintra.com/api/trading}"

echo "🔗 Using Trading Engine URL: ${BASE_URL}"
echo ""

echo "🎭 Mock Trading Bot Demo"
echo "========================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Start a bot with mock position
echo -e "${BLUE}Test 1: Starting bot with ETC/USDT (50% capital allocation)${NC}"
echo "-----------------------------------------------------------"
curl -X POST "${BASE_URL}/bot/start" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": 1,
    "strategyId": 1,
    "capitalAllocation": 50,
    "symbol": "ETC/USDT"
  }' | jq '.'

echo ""
echo ""
sleep 2

# Test 2: Start another bot with BTC/USDT
echo -e "${BLUE}Test 2: Starting bot with BTC/USDT (25% capital allocation)${NC}"
echo "------------------------------------------------------------"
curl -X POST "${BASE_URL}/bot/start" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": 1,
    "strategyId": 1,
    "capitalAllocation": 25,
    "symbol": "BTC/USDT"
  }' | jq '.'

echo ""
echo ""
sleep 2

# Test 3: Get trade history
echo -e "${BLUE}Test 3: Fetching trade history${NC}"
echo "--------------------------------"
curl -X GET "${BASE_URL}/trades?limit=10" | jq '.'

echo ""
echo ""
sleep 2

# Test 4: Check positions in database
echo -e "${BLUE}Test 4: Checking positions directly in database${NC}"
echo "------------------------------------------------"
echo -e "${YELLOW}Note: This requires database access${NC}"
echo "Query: SELECT * FROM position WHERE status = 'OPEN';"
echo ""

echo -e "${GREEN}✅ Mock trading demo complete!${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "- Mock mode is enabled via TRADING_MOCK_ENABLED=true"
echo "- When you start a bot, it automatically creates:"
echo "  1. TradingBot record"
echo "  2. Mock TradeOrder (BUY order)"
echo "  3. Mock Position (OPEN status)"
echo ""
echo "- This demonstrates the full trading flow without Binance connectivity"
echo "- Perfect for regional restrictions or testing environments"
