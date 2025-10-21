# PNL Calculation - Backend Implementation

## Overview
Moved PNL (Profit & Loss) calculation logic from frontend to backend to solve CORS issues and improve performance.

## Backend Changes

### 1. **MarketDataService.java** - NEW
Location: `/src/backend/trading-engine/src/main/java/com/alphintra/trading_engine/service/MarketDataService.java`

**Features:**
- Fetches real-time prices from Binance API
- Calculates PNL: `(Current Price - Entry Price) × Quantity`
- Calculates PNL percentage: `((Current - Entry) / Entry) × 100`
- Handles multiple symbols in parallel
- No CORS issues (server-side calls)

**Key Methods:**
```java
BigDecimal getCurrentPrice(String symbol)
Map<String, BigDecimal> getCurrentPrices(List<String> symbols)
BigDecimal calculatePnL(BigDecimal entryPrice, BigDecimal currentPrice, BigDecimal quantity)
BigDecimal calculatePnLPercentage(BigDecimal entryPrice, BigDecimal currentPrice)
```

### 2. **PositionWithPnLDTO.java** - NEW
Location: `/src/backend/trading-engine/src/main/java/com/alphintra/trading_engine/dto/PositionWithPnLDTO.java`

**Fields:**
- All standard position fields
- `currentPrice` - Real-time market price
- `calculatedPnl` - Calculated profit/loss in USDT
- `pnlPercentage` - Percentage gain/loss

### 3. **PositionService.java** - NEW
Location: `/src/backend/trading-engine/src/main/java/com/alphintra/trading_engine/service/PositionService.java`

**Features:**
- Orchestrates position fetching with PNL calculation
- Fetches unique symbols from positions
- Gets current prices for all symbols
- Converts positions to DTOs with calculated PNL
- Handles missing price data gracefully

### 4. **PositionController.java** - UPDATED
Location: `/src/backend/trading-engine/src/main/java/com/alphintra/trading_engine/controller/PositionController.java`

**Changes:**
- Added `PositionService` dependency
- Returns `List<PositionWithPnLDTO>` instead of `List<Position>`
- Both endpoints now include real-time PNL:
  - `GET /api/trading/positions`
  - `GET /api/trading/positions/open`

## Frontend Changes

### **main-panel.tsx** - SIMPLIFIED
Location: `/src/frontend/components/ui/user/trade/main-panel.tsx`

**Removed:**
- `fetchMarketPrices()` function (no longer needed)
- `calculatePositionsPnL()` function (done in backend)
- `marketPrices` state
- All Binance API calls from frontend

**Kept:**
- Polling every 5 seconds
- Live update indicator
- All UI components

**Result:** Cleaner code, faster performance, no CORS issues

## API Response Example

### Before (without PNL):
```json
{
  "id": 22747,
  "symbol": "BTC/USDT",
  "entryPrice": 111036.92,
  "quantity": 0.08,
  "status": "OPEN"
}
```

### After (with PNL):
```json
{
  "id": 22747,
  "symbol": "BTC/USDT",
  "entryPrice": 111036.92,
  "quantity": 0.08,
  "currentPrice": 112500.00,
  "calculatedPnl": 117.05,
  "pnlPercentage": 1.32,
  "status": "OPEN"
}
```

## Benefits

✅ **No CORS Issues** - Server-side calls to Binance API
✅ **Better Performance** - Single API call returns everything
✅ **Centralized Logic** - PNL calculation in one place
✅ **More Accurate** - Direct exchange prices
✅ **Easier to Maintain** - Backend service can be reused
✅ **Security** - No API keys exposed in frontend
✅ **Caching Potential** - Easy to add Redis caching later

## Testing

1. **Start Backend:**
   ```bash
   cd src/backend/trading-engine
   ./mvnw spring-boot:run
   ```

2. **Test Endpoint:**
   ```bash
   curl -X GET "http://localhost:8008/api/trading/positions?userId=62&status=OPEN" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

3. **Expected Response:**
   - Positions with `currentPrice`, `calculatedPnl`, and `pnlPercentage`
   - Real-time data from Binance

## Monitoring

**Backend Logs:**
```
[Trading UI] Fetching positions with PNL for user: 62, status: OPEN
[Trading UI] Fetching prices for 1 unique symbols: [BTC/USDT]
[Trading UI] Got prices for 1 symbols
Position 22747: Entry=111036.92, Current=112500.00, PNL=117.05, PNL%=1.32
```

**Frontend Logs:**
```
[Trading UI] Data loaded: {positions: 1, bots: 5, timestamp: "10:30:45 AM"}
```

## Future Enhancements

1. **Redis Caching** - Cache prices for 1-2 seconds
2. **WebSocket** - Real-time price updates
3. **Multiple Exchanges** - Aggregate prices from multiple sources
4. **Historical PNL** - Track PNL over time
5. **Alerts** - Notify when PNL reaches thresholds
