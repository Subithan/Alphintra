#!/usr/bin/env python3
"""
Database initialization script for the no-code service.
This script creates tables and populates them with sample data.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import psycopg2

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Base, User, NoCodeWorkflow, NoCodeComponent, NoCodeTemplate, NoCodeExecution

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alphintra_user:alphintra_password@localhost:5432/alphintra_db")

def create_database():
    """Create database tables"""
    engine = create_engine(DATABASE_URL)
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    return engine

def create_sample_data(engine):
    """Create sample data for testing"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create sample user
        print("Creating sample user...")
        test_user = User(
            email="test@alphintra.com",
            password_hash="test_hash_123",
            first_name="Test",
            last_name="User",
            is_verified=True,
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Created user: {test_user.email}")
        
        # Create sample components
        print("Creating sample components...")
        
        # Technical Indicators
        sma_component = NoCodeComponent(
            name="sma_indicator",
            display_name="Simple Moving Average",
            description="Calculate Simple Moving Average for price data",
            category="indicator",
            subcategory="trend",
            component_type="technical_indicator",
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "array", "description": "Price data"}
                },
                "required": ["data"]
            },
            output_schema={
                "type": "object", 
                "properties": {
                    "sma": {"type": "array", "description": "SMA values"}
                }
            },
            parameters_schema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 200,
                        "default": 20,
                        "description": "Moving average period"
                    }
                }
            },
            default_parameters={"period": 20},
            code_template="""
def calculate_sma(data, period={period}):
    import pandas as pd
    if isinstance(data, pd.DataFrame):
        return data['close'].rolling(window=period).mean()
    return pd.Series(data).rolling(window=period).mean()
""",
            imports_required=["pandas"],
            dependencies=[],
            ui_config={
                "width": 200,
                "height": 80,
                "color": "#3b82f6",
                "icon": "📈"
            },
            icon="📈",
            is_builtin=True,
            is_public=True,
            usage_count=0,
            rating=4.5
        )
        
        rsi_component = NoCodeComponent(
            name="rsi_indicator",
            display_name="RSI Indicator",
            description="Calculate Relative Strength Index",
            category="indicator",
            subcategory="momentum",
            component_type="technical_indicator",
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "array", "description": "Price data"}
                },
                "required": ["data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "rsi": {"type": "array", "description": "RSI values"}
                }
            },
            parameters_schema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 14,
                        "description": "RSI period"
                    }
                }
            },
            default_parameters={"period": 14},
            code_template="""
def calculate_rsi(data, period={period}):
    import pandas as pd
    import numpy as np
    
    if isinstance(data, pd.DataFrame):
        prices = data['close']
    else:
        prices = pd.Series(data)
    
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
""",
            imports_required=["pandas", "numpy"],
            dependencies=[],
            ui_config={
                "width": 200,
                "height": 80,
                "color": "#8b5cf6",
                "icon": "📊"
            },
            icon="📊",
            is_builtin=True,
            is_public=True,
            usage_count=0,
            rating=4.7
        )
        
        # Condition Components
        price_condition = NoCodeComponent(
            name="price_condition",
            display_name="Price Condition",
            description="Check price-based trading conditions",
            category="condition",
            subcategory="price",
            component_type="condition",
            input_schema={
                "type": "object",
                "properties": {
                    "current_price": {"type": "number"},
                    "indicator_value": {"type": "number"}
                },
                "required": ["current_price", "indicator_value"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "condition_met": {"type": "boolean"}
                }
            },
            parameters_schema={
                "type": "object",
                "properties": {
                    "operator": {
                        "type": "string",
                        "enum": [">", "<", ">=", "<=", "==", "cross_above", "cross_below"],
                        "default": ">",
                        "description": "Comparison operator"
                    },
                    "threshold": {
                        "type": "number",
                        "default": 0,
                        "description": "Threshold value"
                    }
                }
            },
            default_parameters={"operator": ">", "threshold": 0},
            code_template="""
def check_price_condition(current_price, indicator_value, operator='{operator}', threshold={threshold}):
    if operator == '>':
        return current_price > indicator_value + threshold
    elif operator == '<':
        return current_price < indicator_value - threshold
    elif operator == '>=':
        return current_price >= indicator_value + threshold
    elif operator == '<=':
        return current_price <= indicator_value - threshold
    elif operator == '==':
        return abs(current_price - indicator_value) <= threshold
    elif operator == 'cross_above':
        return current_price > indicator_value
    elif operator == 'cross_below':
        return current_price < indicator_value
    return False
""",
            imports_required=[],
            dependencies=[],
            ui_config={
                "width": 200,
                "height": 100,
                "color": "#f59e0b",
                "icon": "🎯"
            },
            icon="🎯",
            is_builtin=True,
            is_public=True,
            usage_count=0,
            rating=4.3
        )
        
        # Action Components
        buy_signal = NoCodeComponent(
            name="buy_signal",
            display_name="Buy Signal",
            description="Generate buy trading signals",
            category="action",
            subcategory="trading",
            component_type="action",
            input_schema={
                "type": "object",
                "properties": {
                    "condition": {"type": "boolean"}
                },
                "required": ["condition"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "signal": {"type": "object"}
                }
            },
            parameters_schema={
                "type": "object",
                "properties": {
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "default": 100,
                        "description": "Order quantity"
                    },
                    "order_type": {
                        "type": "string",
                        "enum": ["market", "limit"],
                        "default": "market",
                        "description": "Order type"
                    }
                }
            },
            default_parameters={"quantity": 100, "order_type": "market"},
            code_template="""
def generate_buy_signal(condition, quantity={quantity}, order_type='{order_type}'):
    import pandas as pd
    if condition:
        return {
            'action': 'buy',
            'quantity': quantity,
            'order_type': order_type,
            'timestamp': pd.Timestamp.now()
        }
    return None
""",
            imports_required=["pandas"],
            dependencies=[],
            ui_config={
                "width": 180,
                "height": 80,
                "color": "#10b981",
                "icon": "📈"
            },
            icon="📈",
            is_builtin=True,
            is_public=True,
            usage_count=0,
            rating=4.6
        )
        
        sell_signal = NoCodeComponent(
            name="sell_signal",
            display_name="Sell Signal",
            description="Generate sell trading signals",
            category="action",
            subcategory="trading",
            component_type="action",
            input_schema={
                "type": "object",
                "properties": {
                    "condition": {"type": "boolean"}
                },
                "required": ["condition"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "signal": {"type": "object"}
                }
            },
            parameters_schema={
                "type": "object",
                "properties": {
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "default": 100,
                        "description": "Order quantity"
                    },
                    "order_type": {
                        "type": "string",
                        "enum": ["market", "limit"],
                        "default": "market",
                        "description": "Order type"
                    }
                }
            },
            default_parameters={"quantity": 100, "order_type": "market"},
            code_template="""
def generate_sell_signal(condition, quantity={quantity}, order_type='{order_type}'):
    import pandas as pd
    if condition:
        return {
            'action': 'sell',
            'quantity': quantity,
            'order_type': order_type,
            'timestamp': pd.Timestamp.now()
        }
    return None
""",
            imports_required=["pandas"],
            dependencies=[],
            ui_config={
                "width": 180,
                "height": 80,
                "color": "#ef4444",
                "icon": "📉"
            },
            icon="📉",
            is_builtin=True,
            is_public=True,
            usage_count=0,
            rating=4.6
        )
        
        components = [sma_component, rsi_component, price_condition, buy_signal, sell_signal]
        for component in components:
            db.add(component)
        
        db.commit()
        print(f"✅ Created {len(components)} sample components")
        
        # Create sample templates
        print("Creating sample templates...")
        
        # Simple RSI Strategy Template
        rsi_strategy_template = NoCodeTemplate(
            name="RSI Mean Reversion Strategy",
            description="A simple RSI-based mean reversion trading strategy",
            category="momentum",
            difficulty_level="beginner",
            template_data={
                "nodes": [
                    {
                        "id": "data-1",
                        "type": "market_data_input",
                        "position": {"x": 100, "y": 100},
                        "data": {
                            "label": "Market Data",
                            "parameters": {
                                "symbol": "BTCUSDT",
                                "timeframe": "1h"
                            }
                        }
                    },
                    {
                        "id": "rsi-1", 
                        "type": "rsi_indicator",
                        "position": {"x": 300, "y": 100},
                        "data": {
                            "label": "RSI (14)",
                            "parameters": {
                                "period": 14
                            }
                        }
                    },
                    {
                        "id": "buy-condition-1",
                        "type": "indicator_condition",
                        "position": {"x": 500, "y": 50},
                        "data": {
                            "label": "RSI < 30",
                            "parameters": {
                                "operator": "<",
                                "threshold": 30
                            }
                        }
                    },
                    {
                        "id": "sell-condition-1",
                        "type": "indicator_condition", 
                        "position": {"x": 500, "y": 150},
                        "data": {
                            "label": "RSI > 70",
                            "parameters": {
                                "operator": ">",
                                "threshold": 70
                            }
                        }
                    },
                    {
                        "id": "buy-action-1",
                        "type": "buy_signal",
                        "position": {"x": 700, "y": 50},
                        "data": {
                            "label": "Buy Signal",
                            "parameters": {
                                "quantity": 100,
                                "order_type": "market"
                            }
                        }
                    },
                    {
                        "id": "sell-action-1",
                        "type": "sell_signal",
                        "position": {"x": 700, "y": 150},
                        "data": {
                            "label": "Sell Signal",
                            "parameters": {
                                "quantity": 100,
                                "order_type": "market"
                            }
                        }
                    }
                ],
                "edges": [
                    {
                        "id": "e1",
                        "source": "data-1",
                        "target": "rsi-1"
                    },
                    {
                        "id": "e2",
                        "source": "rsi-1",
                        "target": "buy-condition-1"
                    },
                    {
                        "id": "e3",
                        "source": "rsi-1",
                        "target": "sell-condition-1"
                    },
                    {
                        "id": "e4",
                        "source": "buy-condition-1",
                        "target": "buy-action-1"
                    },
                    {
                        "id": "e5",
                        "source": "sell-condition-1",
                        "target": "sell-action-1"
                    }
                ]
            },
            author_id=test_user.id,
            is_featured=True,
            is_public=True,
            usage_count=0,
            rating=4.2,
            keywords=["rsi", "mean-reversion", "momentum", "beginner"],
            estimated_time_minutes=15,
            expected_performance={
                "avg_return": 12.5,
                "win_rate": 65.0,
                "max_drawdown": -8.2,
                "sharpe_ratio": 1.3
            }
        )
        
        # Moving Average Crossover Template
        ma_crossover_template = NoCodeTemplate(
            name="Moving Average Crossover Strategy",
            description="Classic dual moving average crossover strategy",
            category="trend",
            difficulty_level="beginner",
            template_data={
                "nodes": [
                    {
                        "id": "data-1",
                        "type": "market_data_input",
                        "position": {"x": 100, "y": 100},
                        "data": {
                            "label": "Market Data",
                            "parameters": {
                                "symbol": "ETHUSDT",
                                "timeframe": "1d"
                            }
                        }
                    },
                    {
                        "id": "sma-fast-1",
                        "type": "sma_indicator",
                        "position": {"x": 300, "y": 50},
                        "data": {
                            "label": "SMA Fast (10)",
                            "parameters": {
                                "period": 10
                            }
                        }
                    },
                    {
                        "id": "sma-slow-1",
                        "type": "sma_indicator",
                        "position": {"x": 300, "y": 150},
                        "data": {
                            "label": "SMA Slow (20)",
                            "parameters": {
                                "period": 20
                            }
                        }
                    },
                    {
                        "id": "crossover-condition-1",
                        "type": "price_condition",
                        "position": {"x": 500, "y": 100},
                        "data": {
                            "label": "Fast > Slow",
                            "parameters": {
                                "operator": "cross_above",
                                "threshold": 0
                            }
                        }
                    },
                    {
                        "id": "buy-action-1",
                        "type": "buy_signal",
                        "position": {"x": 700, "y": 100},
                        "data": {
                            "label": "Buy on Crossover",
                            "parameters": {
                                "quantity": 100,
                                "order_type": "market"
                            }
                        }
                    }
                ],
                "edges": [
                    {
                        "id": "e1",
                        "source": "data-1",
                        "target": "sma-fast-1"
                    },
                    {
                        "id": "e2",
                        "source": "data-1", 
                        "target": "sma-slow-1"
                    },
                    {
                        "id": "e3",
                        "source": "sma-fast-1",
                        "target": "crossover-condition-1"
                    },
                    {
                        "id": "e4",
                        "source": "sma-slow-1",
                        "target": "crossover-condition-1"
                    },
                    {
                        "id": "e5",
                        "source": "crossover-condition-1",
                        "target": "buy-action-1"
                    }
                ]
            },
            author_id=test_user.id,
            is_featured=True,
            is_public=True,
            usage_count=0,
            rating=4.0,
            keywords=["moving-average", "crossover", "trend", "beginner"],
            estimated_time_minutes=10,
            expected_performance={
                "avg_return": 8.7,
                "win_rate": 58.0,
                "max_drawdown": -12.1,
                "sharpe_ratio": 0.9
            }
        )
        
        templates = [rsi_strategy_template, ma_crossover_template]
        for template in templates:
            db.add(template)
        
        db.commit()
        print(f"✅ Created {len(templates)} sample templates")
        
        # Create sample workflows
        print("Creating sample workflows...")
        
        sample_workflow = NoCodeWorkflow(
            name="My First Strategy",
            description="A simple demo strategy for testing",
            category="demo",
            tags=["demo", "test", "sample"],
            user_id=test_user.id,
            workflow_data={
                "nodes": [
                    {
                        "id": "data-input-1",
                        "type": "market_data_input",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "label": "Market Data Input",
                            "parameters": {
                                "symbol": "BTCUSDT",
                                "timeframe": "1h"
                            }
                        }
                    },
                    {
                        "id": "sma-1",
                        "type": "sma_indicator", 
                        "position": {"x": 350, "y": 200},
                        "data": {
                            "label": "SMA (20)",
                            "parameters": {
                                "period": 20
                            }
                        }
                    }
                ],
                "edges": [
                    {
                        "id": "edge-1",
                        "source": "data-input-1",
                        "target": "sma-1"
                    }
                ]
            },
            execution_mode="backtest",
            compilation_status="pending",
            validation_status="pending",
            deployment_status="draft",
            is_template=False,
            is_public=False,
            version=1,
            total_executions=0,
            successful_executions=0
        )
        
        db.add(sample_workflow)
        db.commit()
        db.refresh(sample_workflow)
        print(f"✅ Created sample workflow: {sample_workflow.name}")
        
        # Create sample execution
        print("Creating sample execution...")
        
        sample_execution = NoCodeExecution(
            workflow_id=sample_workflow.id,
            user_id=test_user.id,
            execution_type="backtest",
            symbols=["BTCUSDT"],
            timeframe="1h",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            initial_capital=10000.0,
            status="completed",
            progress=100,
            current_step="Completed",
            final_capital=11250.0,
            total_return=1250.0,
            total_return_percent=12.5,
            sharpe_ratio=1.8,
            max_drawdown_percent=-5.2,
            total_trades=25,
            winning_trades=18,
            trades_data=[
                {
                    "entry_price": 45000,
                    "exit_price": 46500,
                    "quantity": 0.1,
                    "pnl": 150,
                    "entry_time": "2023-01-01T10:00:00",
                    "exit_time": "2023-01-01T12:00:00"
                }
            ],
            performance_metrics={
                "sharpe_ratio": 1.8,
                "max_drawdown": -5.2,
                "win_rate": 72.0,
                "profit_factor": 2.1,
                "avg_win": 95.5,
                "avg_loss": -45.2
            },
            execution_logs=[],
            error_logs=[],
            completed_at=datetime.now()
        )
        
        db.add(sample_execution)
        db.commit()
        print(f"✅ Created sample execution with {sample_execution.total_trades} trades")
        
        print("🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

# --- Database bootstrap logic ---
DB_NAME = "alphintra_nocode_service"
DB_USER = "nocode_service_user"
DB_PASSWORD = "alphintra@123"
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")

# Connect to default 'postgres' DB to create the target DB if needed
try:
    conn = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    exists = cur.fetchone()
    if not exists:
        print(f"Creating database '{DB_NAME}'...")
        cur.execute(f"CREATE DATABASE \"{DB_NAME}\"")
        print(f"✅ Database '{DB_NAME}' created.")
    else:
        print(f"Database '{DB_NAME}' already exists.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error ensuring database exists: {e}")
    sys.exit(1)

# Now set DATABASE_URL for SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def main():
    """Main initialization function"""
    print("🚀 Initializing Alphintra No-Code Service Database...")
    
    try:
        # Create database tables
        engine = create_database()
        
        # Create sample data
        create_sample_data(engine)
        
        print("\n" + "="*50)
        print("✅ Database initialization completed successfully!")
        print("You can now start the no-code service.")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()