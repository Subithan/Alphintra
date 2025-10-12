curl -X POST http://localhost:8008/api/trading/bot/start \
-H "Content-Type: application/json" \
-d '{"userId": 1, "strategyId": 1}'

ocker compose -f docker-compose.minimal.yml build trading-engine 