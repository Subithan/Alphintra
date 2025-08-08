"""
Strategy management service for business logic operations.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.strategy import Strategy, StrategyStatus, StrategyVersion, StrategyPerformanceMetrics
from app.services.execution_engine import ExecutionEngine
from app.sdk.strategy import StrategyContext
from app.sdk.data import MarketData
from app.sdk.portfolio import Portfolio
from app.sdk.orders import OrderManager
from app.sdk.risk import RiskManager


class StrategyService:
    """Service for managing strategies and their lifecycle."""
    
    def __init__(self, execution_engine: ExecutionEngine):
        self.execution_engine = execution_engine
        self.logger = logging.getLogger(__name__)
    
    async def create_strategy(self, strategy_data: Dict[str, Any], 
                            user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Create a new strategy."""
        try:
            # Validate strategy code
            validation_result = self.execution_engine.validate_strategy_code(
                strategy_data["code"]
            )
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Strategy code validation failed",
                    "validation_errors": validation_result["errors"]
                }
            
            # Create strategy
            strategy = Strategy(
                name=strategy_data["name"],
                description=strategy_data.get("description"),
                code=strategy_data["code"],
                sdk_version="1.0.0",
                parameters=strategy_data.get("parameters", {}),
                status=StrategyStatus.DRAFT,
                user_id=UUID(user_id),
                tags=strategy_data.get("tags", [])
            )
            
            db.add(strategy)
            await db.commit()
            await db.refresh(strategy)
            
            # Create initial version
            await self._create_strategy_version(strategy, db)
            
            self.logger.info(f"Strategy created: {strategy.name} by {user_id}")
            
            return {
                "success": True,
                "strategy_id": str(strategy.id),
                "validation_warnings": validation_result.get("warnings", [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create strategy: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_strategy(self, strategy_id: str, user_id: str, 
                         db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get a strategy by ID."""
        try:
            result = await db.execute(
                select(Strategy).where(
                    and_(
                        Strategy.id == UUID(strategy_id),
                        Strategy.user_id == UUID(user_id)
                    )
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return None
            
            return self._strategy_to_dict(strategy)
            
        except Exception as e:
            self.logger.error(f"Failed to get strategy: {str(e)}")
            return None
    
    async def list_strategies(self, filters: Dict[str, Any], db: AsyncSession) -> List[Dict[str, Any]]:
        """List strategies with optional filtering."""
        try:
            query = select(Strategy).where(Strategy.user_id == UUID(filters["user_id"]))
            
            # Apply filters
            if filters.get("status"):
                query = query.where(Strategy.status == StrategyStatus(filters["status"]))
            
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                search_conditions = [
                    Strategy.name.ilike(search_term),
                    Strategy.description.ilike(search_term)
                ]
                query = query.where(or_(*search_conditions))
            
            # Apply sorting
            sort_by = filters.get("sort_by", "created_at")
            sort_order = filters.get("sort_order", "desc")
            
            if sort_by == "name":
                order_column = Strategy.name
            elif sort_by == "updated_at":
                order_column = Strategy.updated_at
            else:
                order_column = Strategy.created_at
            
            if sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
            
            # Apply pagination
            limit = filters.get("limit", 50)
            offset = filters.get("offset", 0)
            query = query.limit(limit).offset(offset)
            
            result = await db.execute(query)
            strategies = result.scalars().all()
            
            return [self._strategy_to_dict(strategy) for strategy in strategies]
            
        except Exception as e:
            self.logger.error(f"Failed to list strategies: {str(e)}")
            return []
    
    async def update_strategy(self, strategy_id: str, update_data: Dict[str, Any],
                            user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Update an existing strategy."""
        try:
            # Get strategy
            result = await db.execute(
                select(Strategy).where(
                    and_(
                        Strategy.id == UUID(strategy_id),
                        Strategy.user_id == UUID(user_id)
                    )
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return {"success": False, "error": "Strategy not found"}
            
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
            
            # Store current version if code changed
            code_changed = "code" in update_data and update_data["code"] != strategy.code
            
            # Update strategy
            for field, value in update_data.items():
                if hasattr(strategy, field):
                    if field == "status" and isinstance(value, str):
                        setattr(strategy, field, StrategyStatus(value))
                    else:
                        setattr(strategy, field, value)
            
            strategy.updated_at = datetime.now()
            
            # Create new version if code changed
            if code_changed:
                await self._create_strategy_version(strategy, db)
            
            await db.commit()
            
            self.logger.info(f"Strategy updated: {strategy_id} by {user_id}")
            
            return {
                "success": True,
                "validation_warnings": validation_result.get("warnings", []) if "code" in update_data else []
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update strategy: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def delete_strategy(self, strategy_id: str, user_id: str, 
                            db: AsyncSession) -> Dict[str, Any]:
        """Delete a strategy."""
        try:
            # Get strategy
            result = await db.execute(
                select(Strategy).where(
                    and_(
                        Strategy.id == UUID(strategy_id),
                        Strategy.user_id == UUID(user_id)
                    )
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return {"success": False, "error": "Strategy not found"}
            
            # Soft delete - mark as archived
            strategy.status = StrategyStatus.ARCHIVED
            strategy.updated_at = datetime.now()
            
            await db.commit()
            
            self.logger.info(f"Strategy archived: {strategy_id} by {user_id}")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Failed to delete strategy: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def execute_strategy(self, strategy_id: str, execution_config: Dict[str, Any],
                             user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Execute a strategy with given configuration."""
        try:
            # Get strategy
            strategy = await self.get_strategy(strategy_id, user_id, db)
            if not strategy:
                return {"success": False, "error": "Strategy not found"}
            
            # Create execution context
            market_data = MarketData()
            initial_capital = execution_config.get("initial_capital", 100000.0)
            portfolio = Portfolio(initial_capital=initial_capital)
            order_manager = OrderManager(portfolio)
            risk_manager = RiskManager(portfolio)
            
            context = StrategyContext(
                market_data=market_data,
                portfolio=portfolio,
                order_manager=order_manager,
                risk_manager=risk_manager,
                strategy_id=strategy_id,
                user_id=user_id,
                parameters=execution_config.get("parameters", {})
            )
            
            # Execute strategy
            execution_result = self.execution_engine.execute_strategy(
                strategy_code=strategy["code"],
                strategy_context=context,
                execution_id=f"exec_{strategy_id}_{int(datetime.now().timestamp())}"
            )
            
            if execution_result["success"]:
                # Store execution results (simplified)
                return {
                    "success": True,
                    "execution_id": execution_result["execution_id"],
                    "result": execution_result["result"]
                }
            else:
                return {
                    "success": False,
                    "error": execution_result["error"]
                }
            
        except Exception as e:
            self.logger.error(f"Failed to execute strategy: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_strategy_executions(self, strategy_id: str, user_id: str,
                                    limit: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get execution history for a strategy."""
        try:
            # For now, return execution stats from the execution engine
            # In production, this would query execution history from database
            execution_stats = self.execution_engine.get_execution_stats()
            
            return [
                {
                    "execution_id": f"exec_{strategy_id}_{i}",
                    "strategy_id": strategy_id,
                    "status": "completed",
                    "created_at": datetime.now().isoformat(),
                    "execution_time": execution_stats.get("average_execution_time", 0),
                    "result_summary": "Execution completed successfully"
                }
                for i in range(min(limit, 5))  # Mock data
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get strategy executions: {str(e)}")
            return []
    
    async def get_strategy_performance(self, strategy_id: str, user_id: str,
                                     db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get strategy performance metrics."""
        try:
            result = await db.execute(
                select(StrategyPerformanceMetrics).where(
                    StrategyPerformanceMetrics.strategy_id == UUID(strategy_id)
                ).order_by(StrategyPerformanceMetrics.created_at.desc()).limit(1)
            )
            
            performance = result.scalar_one_or_none()
            
            if not performance:
                return None
            
            return {
                "strategy_id": str(performance.strategy_id),
                "total_return": float(performance.total_return),
                "annualized_return": float(performance.annualized_return),
                "max_drawdown": float(performance.max_drawdown),
                "sharpe_ratio": performance.sharpe_ratio,
                "win_rate": performance.win_rate,
                "total_trades": performance.total_trades,
                "created_at": performance.created_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get strategy performance: {str(e)}")
            return None
    
    async def clone_strategy(self, strategy_id: str, user_id: str,
                           clone_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Clone an existing strategy."""
        try:
            # Get original strategy
            original = await self.get_strategy(strategy_id, user_id, db)
            if not original:
                return {"success": False, "error": "Strategy not found"}
            
            # Create cloned strategy data
            cloned_data = {
                "name": clone_data.get("name", f"{original['name']} - Copy"),
                "description": clone_data.get("description", original.get("description")),
                "code": original["code"],
                "parameters": original.get("parameters", {}),
                "tags": original.get("tags", [])
            }
            
            # Create new strategy
            result = await self.create_strategy(cloned_data, user_id, db)
            
            if result["success"]:
                self.logger.info(f"Strategy cloned: {strategy_id} -> {result['strategy_id']} by {user_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to clone strategy: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _create_strategy_version(self, strategy: Strategy, db: AsyncSession):
        """Create a new version record for the strategy."""
        try:
            # Get next version number
            result = await db.execute(
                select(func.max(StrategyVersion.version_number))
                .where(StrategyVersion.strategy_id == strategy.id)
            )
            max_version = result.scalar() or 0
            
            # Mark previous versions as not current
            await db.execute(
                update(StrategyVersion)
                .where(StrategyVersion.strategy_id == strategy.id)
                .values(is_current=False)
            )
            
            # Create new version
            version = StrategyVersion(
                strategy_id=strategy.id,
                user_id=strategy.user_id,
                version_number=max_version + 1,
                code=strategy.code,
                parameters=strategy.parameters,
                change_summary="Code updated",
                is_current=True
            )
            
            db.add(version)
            await db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to create strategy version: {str(e)}")
    
    def _strategy_to_dict(self, strategy: Strategy) -> Dict[str, Any]:
        """Convert strategy model to dictionary."""
        return {
            "id": str(strategy.id),
            "name": strategy.name,
            "description": strategy.description,
            "code": strategy.code,
            "language": strategy.language,
            "sdk_version": strategy.sdk_version,
            "parameters": strategy.parameters,
            "status": strategy.status.value,
            "tags": strategy.tags,
            "total_return": float(strategy.total_return) if strategy.total_return else None,
            "max_drawdown": float(strategy.max_drawdown) if strategy.max_drawdown else None,
            "sharpe_ratio": strategy.sharpe_ratio,
            "win_rate": strategy.win_rate,
            "user_id": str(strategy.user_id),
            "created_at": strategy.created_at.isoformat(),
            "updated_at": strategy.updated_at.isoformat()
        }
    
    async def get_strategy_stats(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Get strategy statistics for a user."""
        try:
            # Total strategies
            total_result = await db.execute(
                select(func.count()).select_from(Strategy)
                .where(Strategy.user_id == UUID(user_id))
            )
            total_strategies = total_result.scalar()
            
            # Strategies by status
            status_result = await db.execute(
                select(Strategy.status, func.count())
                .where(Strategy.user_id == UUID(user_id))
                .group_by(Strategy.status)
            )
            status_stats = {status.value: count for status, count in status_result.all()}
            
            # Recent strategies
            recent_result = await db.execute(
                select(Strategy.name, Strategy.created_at)
                .where(Strategy.user_id == UUID(user_id))
                .order_by(Strategy.created_at.desc())
                .limit(5)
            )
            recent_strategies = [
                {"name": name, "created_at": created_at.isoformat()}
                for name, created_at in recent_result.all()
            ]
            
            return {
                "total_strategies": total_strategies,
                "status_distribution": status_stats,
                "recent_strategies": recent_strategies
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get strategy stats: {str(e)}")
            return {}