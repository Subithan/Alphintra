
docker compose -f docker-compose.minimal.yml build trading-engine 

Step 1: Start Bot
└─> curl with capitalAllocation=50, symbol=BTC/USDT

Step 2: Bot Checks Balance
└─> You have: $2,000 USDT
└─> Allocation: 50%
└─> To Use: $1,000 USDT

Step 3: BUY Signal Triggered
└─> BTC Price: $60,000
└─> Buys: $1,000 ÷ $60,000 = 0.01666 BTC
└─> Position Opened at Entry Price: $60,000

Step 4: Bot Monitors Price
├─> Take Profit Target: $60,000 × 1.03 = $61,800
├─> Stop Loss Target: $60,000 × 0.98 = $58,800
└─> Current Price: $60,500 → HOLD 🧘

Step 5a: PROFIT Scenario
└─> Price reaches $61,850 → SELL! 💰
└─> Profit: $30 (3% gain)
└─> New USDT Balance: $2,030

Step 5b: LOSS Scenario
└─> Price drops to $58,700 → SELL! ⚠️
└─> Loss: -$20 (2% loss)
└─> New USDT Balance: $1,980


curl -X POST http://localhost:8008/api/trading/bot/start \
-H "Content-Type: application/json" \
-d '{"userId": 2, "strategyId": 1, "capitalAllocation": 25, "symbol": "BTC/USDT"}'



Think of it like money denominations - you can't pay $1.237 in cash because the smallest unit is $0.01 (penny). Similarly, each crypto has a minimum tradeable unit.
Step Size: 0.00001 BTC

✅ Valid Orders:
- 0.00001 BTC
- 0.00010 BTC
- 0.12345 BTC

❌ Invalid Orders:
- 0.000001 BTC (too small - below step size)
- 0.123456 BTC (too many decimals - not a multiple of 0.00001)

Current ETC Price: $16.38
Capital to Spend: $100 USDT
ETC Step Size: 0.01

Step 1: Calculate Raw Quantity
$100 ÷ $16.38 = 6.1050... ETC

Step 2: Adjust to Step Size
6.1050 ÷ 0.01 = 610.50 steps
Round DOWN to 610 steps
610 × 0.01 = 6.10 ETC ✅

Step 3: Final Order
Buy exactly 6.10 ETC with $99.918 USDT
(Remaining $0.082 USDT stays in wallet)

Without Adjustment:
Order: 6.1050 ETC
Exchange Response: ❌ ERROR - Invalid quantity precision

With Adjustment:
Order: 6.10 ETC
Exchange Response: ✅ SUCCESS - Order filled

daninithi@DANIs-MacBook-Air docker % docker exec alphintra-minimal-postgres psql -U alphintra -d alphintra_trading_engine -c "SELECT * FROM positions WHERE status='OPEN';"

WalletCredentialsDTO credentials = new WalletCredentialsDTO(
            "HCwZWzdNFNVj6jYlunDyqh1tFScpTnxktaPLGDkZDaorhhQRoq5LGFReqQYN8Fbi",
            "1hbOBVTw20W1tOFSdXgn1VZBtQ8DWzrwC4w5p4CnfUDnGH5aRyhP7Ys6KOFuDzoq"
);


API Key: mUYDoV3S2SmePZPyE6VreXJmgL9QHi8T5wd70Jr2n63Z5VdhCDQdHrOsXxv6gplv

Secret Key: eWZVKMxX6NmXMEtpKBZZxAaKDTypQ2wcJLOokyNz9zUyR4iSPnel5PzYfitD8nUF
