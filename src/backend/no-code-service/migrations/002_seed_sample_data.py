"""
Migration: Seed sample data
Date: 2025-09-22
Description: Populate database with sample components, templates, and test user
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import User, NoCodeComponent, NoCodeTemplate  # noqa: E402

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alphintra_user:alphintra_password@localhost:5432/alphintra_db")
SEED_SAMPLE_DATA = os.getenv("SEED_SAMPLE_DATA", "true").lower() == "true"


def upgrade():
    """Apply sample data seeding"""
    if not SEED_SAMPLE_DATA:
        print("SEED_SAMPLE_DATA=false; skipping sample data seeding migration.")
        return
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("Starting migration: Seed sample data...")

        # Create sample user if it doesn't exist
        print("1. Creating sample user...")
        test_user = db.query(User).filter(User.email == "test@alphintra.com").first()
        if not test_user:
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
            print(f"   ✅ Created user: {test_user.email}")
        else:
            print("   ⚠️ Test user already exists, skipping")

        # Check if sample components already exist
        if db.query(NoCodeComponent).filter(NoCodeComponent.name == "sma_indicator").first():
            print("   ⚠️ Sample components already exist, skipping component seeding")
        else:
            # Create sample components
            print("2. Creating sample technical indicators...")

            # Simple Moving Average
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

            # RSI Indicator
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

            # Price Condition
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

            # Add all components to session
            db.add_all([sma_component, rsi_component, price_condition])
            print("   ✅ Added technical indicators and conditions")

        # Check if sample templates already exist
        if db.query(NoCodeTemplate).filter(NoCodeTemplate.name == "Basic SMA Strategy").first():
            print("   ⚠️ Sample templates already exist, skipping template seeding")
        else:
            # Create sample templates
            print("3. Creating sample templates...")

            basic_sma_template = NoCodeTemplate(
                name="Basic SMA Strategy",
                description="A simple strategy using SMA crossover signals",
                category="beginner",
                difficulty_level="beginner",
                template_data={
                    "nodes": [
                        {
                            "id": "data_input",
                            "type": "data_input",
                            "position": {"x": 100, "y": 100},
                            "data": {"label": "Market Data"}
                        },
                        {
                            "id": "sma_20",
                            "type": "technical_indicator",
                            "position": {"x": 300, "y": 50},
                            "data": {
                                "label": "SMA 20",
                                "component": "sma_indicator",
                                "parameters": {"period": 20}
                            }
                        },
                        {
                            "id": "sma_50",
                            "type": "technical_indicator",
                            "position": {"x": 300, "y": 150},
                            "data": {
                                "label": "SMA 50",
                                "component": "sma_indicator",
                                "parameters": {"period": 50}
                            }
                        },
                        {
                            "id": "buy_signal",
                            "type": "condition",
                            "position": {"x": 500, "y": 100},
                            "data": {
                                "label": "Buy Signal",
                                "component": "price_condition",
                                "parameters": {"operator": "cross_above"}
                            }
                        }
                    ],
                    "edges": [
                        {"id": "e1", "source": "data_input", "target": "sma_20"},
                        {"id": "e2", "source": "data_input", "target": "sma_50"},
                        {"id": "e3", "source": "sma_20", "target": "buy_signal", "sourceHandle": "sma", "targetHandle": "current_price"},
                        {"id": "e4", "source": "sma_50", "target": "buy_signal", "sourceHandle": "sma", "targetHandle": "indicator_value"}
                    ]
                },
                author_id=test_user.id,
                is_featured=True,
                is_public=True,
                keywords=["sma", "crossover", "beginner"],
                estimated_time_minutes=5,
                expected_performance={"estimated_return": "5-15%", "risk_level": "medium"}
            )

            db.add(basic_sma_template)
            print("   ✅ Added sample template")

        # Commit all changes
        db.commit()
        print("✅ Sample data seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


def downgrade():
    """Rollback sample data seeding"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("Rolling back migration: Seed sample data...")

        # Remove sample templates
        db.query(NoCodeTemplate).filter(NoCodeTemplate.name == "Basic SMA Strategy").delete()

        # Remove sample components
        component_names = ["sma_indicator", "rsi_indicator", "price_condition"]
        db.query(NoCodeComponent).filter(NoCodeComponent.name.in_(component_names)).delete()

        # Remove test user
        db.query(User).filter(User.email == "test@alphintra.com").delete()

        db.commit()
        print("✅ Sample data rollback completed!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error rolling back sample data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()