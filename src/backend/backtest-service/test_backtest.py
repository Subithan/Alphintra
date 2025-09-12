#!/usr/bin/env python3
"""
Test script for the backtest service
"""

import json
import requests
import time

def test_backtest_service():
    """Test the backtest service with a realistic strategy."""
    
    base_url = "http://localhost:8007"
    
    # Test 1: Health check
    print("🔍 Testing backtest service health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Service healthy: {health_data}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backtest service: {e}")
        return
    
    # Test 2: Get available symbols
    print("\n📊 Testing available symbols...")
    try:
        response = requests.get(f"{base_url}/api/backtest/market-data/symbols")
        if response.status_code == 200:
            symbols_data = response.json()
            print(f"✅ Available symbols: {len(symbols_data['symbols'])} symbols")
            print(f"   Timeframes: {symbols_data['timeframes']}")
        else:
            print(f"❌ Symbols request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Symbols request error: {e}")
    
    # Test 3: Simple strategy backtest
    print("\n🚀 Testing simple strategy backtest...")
    
    simple_strategy = '''
# Simple Moving Average Strategy
import pandas as pd
import numpy as np

# Initialize variables
capital = config.initial_capital
positions = {}
trades = []

# Generate simple signals using the provided data
if len(data) > 50:
    # Calculate simple moving averages
    data['sma_20'] = data['close'].rolling(window=20).mean()
    data['sma_50'] = data['close'].rolling(window=50).mean()
    
    # Generate buy/sell signals
    data['signal'] = 0
    data.loc[data['sma_20'] > data['sma_50'], 'signal'] = 1  # Buy signal
    data.loc[data['sma_20'] < data['sma_50'], 'signal'] = -1  # Sell signal
    
    # Simulate some trades
    position = 0
    for i in range(50, len(data)):
        current_signal = data.iloc[i]['signal']
        current_price = data.iloc[i]['close']
        
        if current_signal == 1 and position == 0:  # Buy
            shares = int(capital * 0.1 / current_price)  # Use 10% of capital
            if shares > 0:
                cost = shares * current_price * (1 + config.commission)
                if cost <= capital:
                    capital -= cost
                    position = shares
                    trades.append({
                        'timestamp': data.index[i],
                        'action': 'BUY',
                        'quantity': shares,
                        'price': current_price,
                        'total_cost': cost
                    })
        
        elif current_signal == -1 and position > 0:  # Sell
            proceeds = position * current_price * (1 - config.commission)
            capital += proceeds
            trades.append({
                'timestamp': data.index[i],
                'action': 'SELL',
                'quantity': position,
                'price': current_price,
                'total_cost': proceeds
            })
            position = 0

print(f"Strategy executed: {len(trades)} trades, Final capital: {capital}")
'''
    
    backtest_request = {
        "workflow_id": "test-workflow-123",
        "strategy_code": simple_strategy,
        "config": {
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "initial_capital": 10000,
            "commission": 0.001,
            "symbols": ["AAPL"],
            "timeframe": "1h"
        },
        "metadata": {
            "test_name": "Simple MA Strategy",
            "test_type": "integration_test"
        }
    }
    
    try:
        print("   Sending backtest request...")
        response = requests.post(
            f"{base_url}/api/backtest/run",
            json=backtest_request,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Backtest completed successfully!")
            print(f"   Execution ID: {result['execution_id']}")
            print(f"   Success: {result['success']}")
            
            if result['success']:
                metrics = result['performance_metrics']
                trade_summary = result['trade_summary']
                
                print(f"\n📈 Performance Metrics:")
                print(f"   Total Return: {metrics['total_return']:.2f}")
                print(f"   Total Return %: {metrics['total_return_percent']:.2f}%")
                print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
                print(f"   Max Drawdown %: {metrics['max_drawdown_percent']:.2f}%")
                print(f"   Final Capital: ${metrics['final_capital']:.2f}")
                
                print(f"\n📊 Trade Summary:")
                print(f"   Total Trades: {trade_summary['total_trades']}")
                print(f"   Winning Trades: {trade_summary['winning_trades']}")
                print(f"   Losing Trades: {trade_summary['losing_trades']}")
                
                market_stats = result['market_data_stats']
                print(f"\n📉 Market Data:")
                print(f"   Data Points: {market_stats['data_points']}")
                print(f"   Date Range: {market_stats['date_range']}")
                print(f"   Price Range: {market_stats['price_range']}")
                
            else:
                print(f"❌ Backtest failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Backtest request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Backtest request error: {e}")

    # Test 4: Performance metrics definitions
    print("\n📚 Testing performance metrics definitions...")
    try:
        response = requests.get(f"{base_url}/api/backtest/performance-metrics/definitions")
        if response.status_code == 200:
            definitions = response.json()
            print(f"✅ Got definitions for {len(definitions['metrics'])} metrics")
        else:
            print(f"❌ Definitions request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Definitions request error: {e}")
    
    print("\n🎉 Backtest service testing completed!")


if __name__ == "__main__":
    print("🧪 Backtest Service Integration Test")
    print("=" * 50)
    test_backtest_service()