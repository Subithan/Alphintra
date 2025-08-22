"""
Strategy template management service.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.strategy import StrategyTemplate, DifficultyLevel
from app.services.execution_engine import ExecutionEngine


class TemplateService:
    """Service for managing strategy templates."""
    
    def __init__(self, execution_engine: ExecutionEngine):
        self.execution_engine = execution_engine
        self.logger = logging.getLogger(__name__)
        
        # Built-in template categories
        self.categories = {
            "trend_following": "Trend Following",
            "mean_reversion": "Mean Reversion", 
            "momentum": "Momentum",
            "arbitrage": "Arbitrage",
            "market_making": "Market Making",
            "multi_asset": "Multi-Asset",
            "risk_parity": "Risk Parity",
            "pairs_trading": "Pairs Trading",
            "machine_learning": "Machine Learning",
            "technical_analysis": "Technical Analysis"
        }
    
    async def create_template(self, template_data: Dict[str, Any], 
                            author_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Create a new strategy template."""
        try:
            # Validate template code
            validation_result = self.execution_engine.validate_strategy_code(
                template_data["code"]
            )
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Template code validation failed",
                    "validation_errors": validation_result["errors"]
                }
            
            # Create template
            template = StrategyTemplate(
                name=template_data["name"],
                description=template_data["description"],
                category=template_data.get("category", "custom"),
                code=template_data["code"],
                parameters=template_data.get("parameters", {}),
                documentation=template_data.get("documentation", ""),
                difficulty_level=DifficultyLevel(template_data.get("difficulty_level", "intermediate")),
                is_public=template_data.get("is_public", False),
                author_id=UUID(author_id),
                tags=template_data.get("tags", [])
            )
            
            db.add(template)
            await db.commit()
            await db.refresh(template)
            
            self.logger.info(f"Template created: {template.name} by {author_id}")
            
            return {
                "success": True,
                "template_id": str(template.id),
                "validation_warnings": validation_result.get("warnings", [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create template: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_template(self, template_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get a template by ID."""
        try:
            result = await db.execute(
                select(StrategyTemplate).where(StrategyTemplate.id == UUID(template_id))
            )
            template = result.scalar_one_or_none()
            
            if not template:
                return None
            
            return self._template_to_dict(template)
            
        except Exception as e:
            self.logger.error(f"Failed to get template: {str(e)}")
            return None
    
    async def list_templates(self, filters: Dict[str, Any], db: AsyncSession) -> List[Dict[str, Any]]:
        """List templates with optional filtering."""
        try:
            query = select(StrategyTemplate)
            
            # Apply filters
            conditions = []
            
            if filters.get("category"):
                conditions.append(StrategyTemplate.category == filters["category"])
            
            if filters.get("difficulty_level"):
                conditions.append(StrategyTemplate.difficulty_level == DifficultyLevel(filters["difficulty_level"]))
            
            if filters.get("is_public") is not None:
                conditions.append(StrategyTemplate.is_public == filters["is_public"])
            
            if filters.get("author_id"):
                conditions.append(StrategyTemplate.author_id == UUID(filters["author_id"]))
            
            if filters.get("tags"):
                # Filter by tags (any of the specified tags)
                tag_conditions = [StrategyTemplate.tags.contains([tag]) for tag in filters["tags"]]
                conditions.append(or_(*tag_conditions))
            
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                search_conditions = [
                    StrategyTemplate.name.ilike(search_term),
                    StrategyTemplate.description.ilike(search_term),
                    StrategyTemplate.documentation.ilike(search_term)
                ]
                conditions.append(or_(*search_conditions))
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Apply sorting
            sort_by = filters.get("sort_by", "created_at")
            sort_order = filters.get("sort_order", "desc")
            
            if sort_by == "name":
                order_column = StrategyTemplate.name
            elif sort_by == "usage_count":
                order_column = StrategyTemplate.usage_count
            elif sort_by == "rating":
                order_column = StrategyTemplate.rating
            else:
                order_column = StrategyTemplate.created_at
            
            if sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
            
            # Apply pagination
            limit = filters.get("limit", 50)
            offset = filters.get("offset", 0)
            query = query.limit(limit).offset(offset)
            
            result = await db.execute(query)
            templates = result.scalars().all()
            
            return [self._template_to_dict(template) for template in templates]
            
        except Exception as e:
            self.logger.error(f"Failed to list templates: {str(e)}")
            return []
    
    async def update_template(self, template_id: str, update_data: Dict[str, Any],
                            user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Update an existing template."""
        try:
            # Get template
            result = await db.execute(
                select(StrategyTemplate).where(StrategyTemplate.id == UUID(template_id))
            )
            template = result.scalar_one_or_none()
            
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Check permissions
            if str(template.author_id) != user_id:
                return {"success": False, "error": "Permission denied"}
            
            # Validate code if provided
            if "code" in update_data:
                validation_result = self.execution_engine.validate_strategy_code(
                    update_data["code"]
                )
                
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": "Code validation failed",
                        "validation_errors": validation_result["errors"]
                    }
            
            # Update template
            for field, value in update_data.items():
                if hasattr(template, field):
                    if field == "difficulty_level" and isinstance(value, str):
                        setattr(template, field, DifficultyLevel(value))
                    else:
                        setattr(template, field, value)
            
            template.updated_at = datetime.now()
            
            await db.commit()
            
            self.logger.info(f"Template updated: {template_id} by {user_id}")
            
            return {
                "success": True,
                "validation_warnings": validation_result.get("warnings", []) if "code" in update_data else []
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update template: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def delete_template(self, template_id: str, user_id: str, 
                            db: AsyncSession) -> Dict[str, Any]:
        """Delete a template."""
        try:
            # Get template
            result = await db.execute(
                select(StrategyTemplate).where(StrategyTemplate.id == UUID(template_id))
            )
            template = result.scalar_one_or_none()
            
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Check permissions
            if str(template.author_id) != user_id:
                return {"success": False, "error": "Permission denied"}
            
            # Delete template
            await db.execute(
                delete(StrategyTemplate).where(StrategyTemplate.id == UUID(template_id))
            )
            await db.commit()
            
            self.logger.info(f"Template deleted: {template_id} by {user_id}")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Failed to delete template: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def clone_template(self, template_id: str, user_id: str, 
                           clone_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Clone a template to create a new strategy."""
        try:
            # Get template
            result = await db.execute(
                select(StrategyTemplate).where(StrategyTemplate.id == UUID(template_id))
            )
            template = result.scalar_one_or_none()
            
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Check if template is public or user owns it
            if not template.is_public and str(template.author_id) != user_id:
                return {"success": False, "error": "Template not accessible"}
            
            # Increment usage count
            template.usage_count += 1
            
            # Create new strategy from template
            from app.models.strategy import Strategy, StrategyStatus
            
            strategy = Strategy(
                name=clone_data.get("name", f"{template.name} - Copy"),
                description=clone_data.get("description", template.description),
                code=template.code,
                sdk_version="1.0.0",
                parameters=template.parameters.copy(),
                status=StrategyStatus.DRAFT,
                user_id=UUID(user_id),
                tags=template.tags.copy()
            )
            
            db.add(strategy)
            await db.commit()
            await db.refresh(strategy)
            
            self.logger.info(f"Template cloned: {template_id} -> strategy {strategy.id} by {user_id}")
            
            return {
                "success": True,
                "strategy_id": str(strategy.id),
                "template_usage_count": template.usage_count
            }
            
        except Exception as e:
            self.logger.error(f"Failed to clone template: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def rate_template(self, template_id: str, rating: float, user_id: str,
                          db: AsyncSession) -> Dict[str, Any]:
        """Rate a template (simplified rating system)."""
        try:
            if not 1.0 <= rating <= 5.0:
                return {"success": False, "error": "Rating must be between 1.0 and 5.0"}
            
            # Get template
            result = await db.execute(
                select(StrategyTemplate).where(StrategyTemplate.id == UUID(template_id))
            )
            template = result.scalar_one_or_none()
            
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # For now, simple average rating (in production, would track individual ratings)
            # This is a simplified implementation
            if template.rating == 0:
                template.rating = rating
            else:
                # Simple weighted average (not ideal, but for demo)
                template.rating = (template.rating + rating) / 2
            
            await db.commit()
            
            self.logger.info(f"Template rated: {template_id} = {rating} by {user_id}")
            
            return {
                "success": True,
                "new_rating": template.rating
            }
            
        except Exception as e:
            self.logger.error(f"Failed to rate template: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_template_categories(self) -> Dict[str, str]:
        """Get available template categories."""
        return self.categories
    
    async def get_template_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get template statistics."""
        try:
            # Total templates
            total_result = await db.execute(
                select(func.count()).select_from(StrategyTemplate)
            )
            total_templates = total_result.scalar()
            
            # Public templates
            public_result = await db.execute(
                select(func.count()).select_from(StrategyTemplate)
                .where(StrategyTemplate.is_public == True)
            )
            public_templates = public_result.scalar()
            
            # Templates by category
            category_result = await db.execute(
                select(StrategyTemplate.category, func.count())
                .group_by(StrategyTemplate.category)
            )
            category_stats = dict(category_result.all())
            
            # Templates by difficulty
            difficulty_result = await db.execute(
                select(StrategyTemplate.difficulty_level, func.count())
                .group_by(StrategyTemplate.difficulty_level)
            )
            difficulty_stats = {level.value: count for level, count in difficulty_result.all()}
            
            # Most popular templates
            popular_result = await db.execute(
                select(StrategyTemplate.name, StrategyTemplate.usage_count)
                .where(StrategyTemplate.is_public == True)
                .order_by(StrategyTemplate.usage_count.desc())
                .limit(10)
            )
            popular_templates = [
                {"name": name, "usage_count": count} 
                for name, count in popular_result.all()
            ]
            
            return {
                "total_templates": total_templates,
                "public_templates": public_templates,
                "private_templates": total_templates - public_templates,
                "category_distribution": category_stats,
                "difficulty_distribution": difficulty_stats,
                "most_popular": popular_templates
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get template stats: {str(e)}")
            return {}
    
    def _template_to_dict(self, template: StrategyTemplate) -> Dict[str, Any]:
        """Convert template model to dictionary."""
        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "code": template.code,
            "parameters": template.parameters,
            "documentation": template.documentation,
            "difficulty_level": template.difficulty_level.value,
            "is_public": template.is_public,
            "author_id": str(template.author_id),
            "usage_count": template.usage_count,
            "rating": template.rating,
            "tags": template.tags,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }


async def create_builtin_templates(db: AsyncSession, template_service: TemplateService):
    """Create built-in strategy templates."""
    
    builtin_templates = [
        {
            "name": "Simple Moving Average Crossover",
            "description": "Basic trend-following strategy using SMA crossover signals",
            "category": "trend_following",
            "difficulty_level": "beginner",
            "is_public": True,
            "tags": ["sma", "crossover", "trend", "beginner"],
            "documentation": """
# Simple Moving Average Crossover Strategy

This strategy uses two simple moving averages to generate buy and sell signals:
- Buy when short MA crosses above long MA
- Sell when short MA crosses below long MA

## Parameters:
- short_period: Period for short moving average (default: 10)
- long_period: Period for long moving average (default: 30)
- symbol: Trading symbol (default: BTCUSD)
- position_percent: Position size as % of portfolio (default: 0.1)

## Usage:
Suitable for trending markets. Best used with additional filters like volume or momentum confirmation.
            """,
            "parameters": {
                "short_period": {"type": "int", "default": 10, "min": 1, "max": 100},
                "long_period": {"type": "int", "default": 30, "min": 2, "max": 200},
                "symbol": {"type": "str", "default": "BTCUSD"},
                "position_percent": {"type": "float", "default": 0.1, "min": 0.01, "max": 1.0}
            },
            "code": '''
from app.sdk import BaseStrategy
from decimal import Decimal

class SimpleMAStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="Simple Moving Average Crossover",
            description="Basic trend-following strategy using SMA crossover"
        )
        self.author = "Alphintra"
        self.tags = ["sma", "crossover", "trend"]
        self.category = "trend_following"
    
    def initialize(self):
        self.short_period = self.get_parameter("short_period", 10)
        self.long_period = self.get_parameter("long_period", 30)
        self.symbol = self.get_parameter("symbol", "BTCUSD")
        self.position_percent = self.get_parameter("position_percent", 0.1)
        
        self.set_variable("position_size", 0)
        self.set_variable("last_signal", None)
        
        self.log(f"Initialized with short_period={self.short_period}, long_period={self.long_period}")
    
    def on_bar(self):
        # Calculate moving averages
        short_ma = self.data.sma(self.symbol, self.short_period)
        long_ma = self.data.sma(self.symbol, self.long_period)
        
        if short_ma is None or long_ma is None:
            return
        
        current_price = self.data.get_current_price(self.symbol)
        position = self.portfolio.get_position(self.symbol)
        current_size = position.quantity if position else Decimal("0")
        
        # Generate signals
        if short_ma > long_ma and current_size <= 0:
            # Buy signal
            if current_size < 0:
                self.orders.market_order(self.symbol, abs(current_size), "buy")
            
            order_size = self.calculate_position_size()
            self.orders.market_order(self.symbol, order_size, "buy")
            self.set_variable("last_signal", "buy")
            self.log(f"BUY signal: {self.symbol} at {current_price}")
            
        elif short_ma < long_ma and current_size >= 0:
            # Sell signal
            if current_size > 0:
                self.orders.market_order(self.symbol, current_size, "sell")
            
            order_size = self.calculate_position_size()
            self.orders.market_order(self.symbol, order_size, "sell")
            self.set_variable("last_signal", "sell")
            self.log(f"SELL signal: {self.symbol} at {current_price}")
        
        # Record metrics
        self.record_metric("short_ma", short_ma)
        self.record_metric("long_ma", long_ma)
        self.record_metric("price", current_price)
    
    def calculate_position_size(self):
        account_value = self.portfolio.total_value
        max_position_value = account_value * Decimal(str(self.position_percent))
        current_price = self.data.get_current_price(self.symbol)
        
        if current_price and current_price > 0:
            return max_position_value / Decimal(str(current_price))
        return Decimal("0")
    
    def get_required_data(self):
        return {
            "symbols": [self.get_parameter("symbol", "BTCUSD")],
            "timeframe": "1h",
            "history_bars": max(self.get_parameter("long_period", 30) + 10, 100),
            "indicators": ["sma"]
        }
            '''
        },
        {
            "name": "RSI Mean Reversion",
            "description": "Mean reversion strategy using RSI oversold/overbought levels",
            "category": "mean_reversion",
            "difficulty_level": "intermediate",
            "is_public": True,
            "tags": ["rsi", "mean_reversion", "oscillator"],
            "documentation": """
# RSI Mean Reversion Strategy

This strategy uses the Relative Strength Index (RSI) to identify oversold and overbought conditions:
- Buy when RSI < oversold_level (default: 30)
- Sell when RSI > overbought_level (default: 70)

## Parameters:
- rsi_period: RSI calculation period (default: 14)
- oversold_level: RSI level for buy signals (default: 30)
- overbought_level: RSI level for sell signals (default: 70)
- symbol: Trading symbol (default: BTCUSD)
            """,
            "parameters": {
                "rsi_period": {"type": "int", "default": 14, "min": 2, "max": 50},
                "oversold_level": {"type": "float", "default": 30, "min": 10, "max": 40},
                "overbought_level": {"type": "float", "default": 70, "min": 60, "max": 90},
                "symbol": {"type": "str", "default": "BTCUSD"}
            },
            "code": '''
from app.sdk import BaseStrategy
from decimal import Decimal

class RSIMeanReversionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="RSI Mean Reversion",
            description="Mean reversion using RSI levels"
        )
        self.author = "Alphintra"
        self.tags = ["rsi", "mean_reversion"]
        self.category = "mean_reversion"
    
    def initialize(self):
        self.rsi_period = self.get_parameter("rsi_period", 14)
        self.oversold = self.get_parameter("oversold_level", 30)
        self.overbought = self.get_parameter("overbought_level", 70)
        self.symbol = self.get_parameter("symbol", "BTCUSD")
        
        self.log(f"RSI strategy initialized: period={self.rsi_period}")
    
    def on_bar(self):
        rsi = self.data.rsi(self.symbol, self.rsi_period)
        
        if rsi is None:
            return
        
        current_price = self.data.get_current_price(self.symbol)
        position = self.portfolio.get_position(self.symbol)
        has_position = position and not position.is_closed()
        
        if rsi < self.oversold and not has_position:
            # Buy on oversold
            order_size = self.calculate_position_size()
            self.orders.market_order(self.symbol, order_size, "buy")
            self.log(f"BUY on oversold RSI: {rsi:.2f}")
            
        elif rsi > self.overbought and has_position:
            # Sell on overbought
            self.orders.market_order(self.symbol, position.quantity, "sell")
            self.log(f"SELL on overbought RSI: {rsi:.2f}")
        
        self.record_metric("rsi", rsi)
        self.record_metric("price", current_price)
    
    def calculate_position_size(self):
        account_value = self.portfolio.total_value
        position_value = account_value * Decimal("0.2")  # 20% position
        current_price = self.data.get_current_price(self.symbol)
        
        if current_price and current_price > 0:
            return position_value / Decimal(str(current_price))
        return Decimal("0")
            '''
        }
    ]
    
    # Create system user for built-in templates
    system_user_id = "00000000-0000-0000-0000-000000000000"
    
    for template_data in builtin_templates:
        # Check if template already exists
        existing = await db.execute(
            select(StrategyTemplate).where(StrategyTemplate.name == template_data["name"])
        )
        
        if not existing.scalar_one_or_none():
            await template_service.create_template(template_data, system_user_id, db)