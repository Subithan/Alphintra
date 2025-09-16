"""
Strategy loader service for retrieving strategies from AI/ML and No-Code databases.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import asyncpg
import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.models.strategies import (
    StrategyPackage, StrategyFile, StrategySource, 
    StrategyStatus, ExecutionMode
)

logger = structlog.get_logger(__name__)


class DatabaseConnectionError(Exception):
    """Database connection error."""
    pass


class StrategyNotFoundError(Exception):
    """Strategy not found error."""
    pass


class StrategyLoader:
    """Service for loading strategies from multiple databases."""
    
    def __init__(self, ai_ml_db_url: str, no_code_db_url: str):
        self.ai_ml_db_url = ai_ml_db_url
        self.no_code_db_url = no_code_db_url
        
        # Database engines
        self.ai_ml_engine = None
        self.no_code_engine = None
        
        # Session makers
        self.ai_ml_session_maker = None
        self.no_code_session_maker = None
        
        # Cache for loaded strategies
        self._strategy_cache: Dict[str, StrategyPackage] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Configuration
        self.cache_ttl_seconds = 300  # 5 minutes
        self.max_cache_size = 100
    
    async def initialize(self) -> None:
        """Initialize database connections."""
        try:
            # Create async engines
            self.ai_ml_engine = create_async_engine(
                self.ai_ml_db_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600
            )
            
            self.no_code_engine = create_async_engine(
                self.no_code_db_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600
            )
            
            # Create session makers
            self.ai_ml_session_maker = sessionmaker(
                self.ai_ml_engine, 
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self.no_code_session_maker = sessionmaker(
                self.no_code_engine,
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            # Test connections
            await self._test_connections()
            
            logger.info("Strategy loader initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize strategy loader", error=str(e))
            raise DatabaseConnectionError(f"Failed to initialize databases: {e}")
    
    async def shutdown(self) -> None:
        """Cleanup database connections."""
        try:
            if self.ai_ml_engine:
                await self.ai_ml_engine.dispose()
            if self.no_code_engine:
                await self.no_code_engine.dispose()
            
            self._strategy_cache.clear()
            self._cache_timestamps.clear()
            
            logger.info("Strategy loader shutdown completed")
            
        except Exception as e:
            logger.error("Error during strategy loader shutdown", error=str(e))
    
    async def load_strategy(self, strategy_id: str, source: StrategySource, 
                          force_reload: bool = False) -> StrategyPackage:
        """
        Load a strategy from the specified source.
        
        Args:
            strategy_id: Strategy identifier
            source: Strategy source (ai_ml or no_code)
            force_reload: Force reload from database
            
        Returns:
            StrategyPackage with strategy data and files
        """
        cache_key = f"{source}:{strategy_id}"
        
        # Check cache first
        if not force_reload and self._is_cached_and_valid(cache_key):
            logger.debug("Loading strategy from cache", strategy_id=strategy_id, source=source)
            return self._strategy_cache[cache_key]
        
        try:
            if source == StrategySource.AI_ML:
                strategy = await self._load_from_ai_ml_service(strategy_id)
            elif source == StrategySource.NO_CODE:
                strategy = await self._load_from_no_code_service(strategy_id)
            else:
                raise ValueError(f"Unknown strategy source: {source}")
            
            # Cache the strategy
            self._cache_strategy(cache_key, strategy)
            
            logger.info("Strategy loaded successfully", 
                       strategy_id=strategy_id, source=source, 
                       files_count=len(strategy.files))
            
            return strategy
            
        except Exception as e:
            logger.error("Failed to load strategy", 
                        strategy_id=strategy_id, source=source, error=str(e))
            raise
    
    async def list_strategies(self, source: Optional[StrategySource] = None,
                            limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List available strategies from all or specified sources.
        
        Args:
            source: Filter by source (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of strategy metadata
        """
        strategies = []
        
        try:
            if source is None or source == StrategySource.AI_ML:
                ai_ml_strategies = await self._list_ai_ml_strategies(limit, offset)
                strategies.extend(ai_ml_strategies)
            
            if source is None or source == StrategySource.NO_CODE:
                no_code_strategies = await self._list_no_code_strategies(limit, offset)
                strategies.extend(no_code_strategies)
            
            # Sort by updated_at descending
            strategies.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            
            # Apply global limit if listing from all sources
            if source is None:
                strategies = strategies[:limit]
            
            logger.info(f"Listed {len(strategies)} strategies", 
                       source=source, limit=limit, offset=offset)
            
            return strategies
            
        except Exception as e:
            logger.error("Failed to list strategies", source=source, error=str(e))
            raise
    
    async def get_strategy_metadata(self, strategy_id: str, 
                                  source: StrategySource) -> Dict[str, Any]:
        """Get strategy metadata without loading full files."""
        try:
            if source == StrategySource.AI_ML:
                return await self._get_ai_ml_metadata(strategy_id)
            elif source == StrategySource.NO_CODE:
                return await self._get_no_code_metadata(strategy_id)
            else:
                raise ValueError(f"Unknown strategy source: {source}")
                
        except Exception as e:
            logger.error("Failed to get strategy metadata",
                        strategy_id=strategy_id, source=source, error=str(e))
            raise
    
    async def _load_from_ai_ml_service(self, strategy_id: str) -> StrategyPackage:
        """Load strategy from AI/ML service database."""
        async with self.ai_ml_session_maker() as session:
            try:
                # Load main strategy record
                strategy_query = text("""
                    SELECT s.id, s.name, s.description, s.code, s.language, s.sdk_version,
                           s.parameters, s.status, s.tags, s.user_id, s.created_at, s.updated_at,
                           s.total_return, s.max_drawdown, s.sharpe_ratio, s.win_rate
                    FROM strategies s 
                    WHERE s.id = :strategy_id
                """)
                
                result = await session.execute(strategy_query, {"strategy_id": strategy_id})
                strategy_row = result.fetchone()
                
                if not strategy_row:
                    raise StrategyNotFoundError(f"Strategy {strategy_id} not found in AI/ML service")
                
                # Load associated project files
                files_query = text("""
                    SELECT pf.file_name, pf.content, pf.file_type, pf.language, 
                           pf.encoding, pf.checksum, pf.file_path
                    FROM project_files pf
                    JOIN projects p ON pf.project_id = p.id
                    WHERE p.user_id = :user_id
                    AND (p.name ILIKE :strategy_name OR p.id::text = :strategy_id)
                    ORDER BY pf.file_name
                """)
                
                files_result = await session.execute(files_query, {
                    "user_id": strategy_row.user_id,
                    "strategy_name": f"%{strategy_row.name}%",
                    "strategy_id": strategy_id
                })
                
                file_rows = files_result.fetchall()
                
                # Build strategy package
                files = {}
                main_file = "main.py"
                requirements = []
                
                # Always include the main strategy code
                files[main_file] = StrategyFile(
                    filename=main_file,
                    content=strategy_row.code,
                    file_type="python",
                    encoding="utf-8",
                    checksum=self._calculate_checksum(strategy_row.code)
                )
                
                # Add project files if any
                for file_row in file_rows:
                    if file_row.file_name == "requirements.txt":
                        requirements = file_row.content.strip().split('\n')
                        
                    files[file_row.file_name] = StrategyFile(
                        filename=file_row.file_name,
                        content=file_row.content,
                        file_type=file_row.file_type or "text",
                        encoding=file_row.encoding or "utf-8",
                        checksum=file_row.checksum
                    )
                
                # Build performance metrics
                performance_metrics = {}
                if strategy_row.total_return is not None:
                    performance_metrics["total_return"] = float(strategy_row.total_return)
                if strategy_row.max_drawdown is not None:
                    performance_metrics["max_drawdown"] = float(strategy_row.max_drawdown)
                if strategy_row.sharpe_ratio is not None:
                    performance_metrics["sharpe_ratio"] = float(strategy_row.sharpe_ratio)
                if strategy_row.win_rate is not None:
                    performance_metrics["win_rate"] = float(strategy_row.win_rate)
                
                return StrategyPackage(
                    strategy_id=str(strategy_row.id),
                    source=StrategySource.AI_ML,
                    name=strategy_row.name,
                    description=strategy_row.description,
                    version="1.0",  # TODO: Get from version table
                    files=files,
                    main_file=main_file,
                    requirements=requirements,
                    parameters=strategy_row.parameters or {},
                    author_id=str(strategy_row.user_id),
                    created_at=strategy_row.created_at,
                    updated_at=strategy_row.updated_at,
                    tags=strategy_row.tags or [],
                    performance_metrics=performance_metrics if performance_metrics else None
                )
                
            except Exception as e:
                await session.rollback()
                raise
    
    async def _load_from_no_code_service(self, strategy_id: str) -> StrategyPackage:
        """Load strategy from No-Code service database."""
        async with self.no_code_session_maker() as session:
            try:
                # Load workflow record
                workflow_query = text("""
                    SELECT nw.id, nw.uuid, nw.name, nw.description, nw.category, nw.tags,
                           nw.generated_code, nw.generated_requirements, nw.parameters,
                           nw.user_id, nw.created_at, nw.updated_at, nw.version,
                           nw.compilation_status, nw.deployment_status
                    FROM nocode_workflows nw 
                    WHERE nw.uuid::text = :strategy_id OR nw.id::text = :strategy_id
                """)
                
                result = await session.execute(workflow_query, {"strategy_id": strategy_id})
                workflow_row = result.fetchone()
                
                if not workflow_row:
                    raise StrategyNotFoundError(f"Workflow {strategy_id} not found in No-Code service")
                
                # Build files dictionary
                files = {}
                main_file = "strategy.py"  # Generated strategies use this name
                
                # Main generated code
                if workflow_row.generated_code:
                    files[main_file] = StrategyFile(
                        filename=main_file,
                        content=workflow_row.generated_code,
                        file_type="python",
                        encoding="utf-8",
                        checksum=self._calculate_checksum(workflow_row.generated_code)
                    )
                else:
                    raise StrategyNotFoundError(f"No generated code found for workflow {strategy_id}")
                
                # Requirements file
                requirements = workflow_row.generated_requirements or []
                if requirements:
                    requirements_content = '\n'.join(requirements)
                    files["requirements.txt"] = StrategyFile(
                        filename="requirements.txt",
                        content=requirements_content,
                        file_type="text",
                        encoding="utf-8",
                        checksum=self._calculate_checksum(requirements_content)
                    )
                
                # Configuration file with parameters
                if workflow_row.parameters:
                    config_content = json.dumps(workflow_row.parameters, indent=2)
                    files["config.json"] = StrategyFile(
                        filename="config.json",
                        content=config_content,
                        file_type="json",
                        encoding="utf-8",
                        checksum=self._calculate_checksum(config_content)
                    )
                
                return StrategyPackage(
                    strategy_id=str(workflow_row.uuid),
                    source=StrategySource.NO_CODE,
                    name=workflow_row.name,
                    description=workflow_row.description,
                    version=f"v{workflow_row.version}",
                    files=files,
                    main_file=main_file,
                    requirements=requirements,
                    parameters=workflow_row.parameters or {},
                    author_id=str(workflow_row.user_id),
                    created_at=workflow_row.created_at,
                    updated_at=workflow_row.updated_at,
                    tags=workflow_row.tags or [],
                    performance_metrics=None  # TODO: Add from execution history
                )
                
            except Exception as e:
                await session.rollback()
                raise
    
    async def _list_ai_ml_strategies(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """List strategies from AI/ML service."""
        async with self.ai_ml_session_maker() as session:
            query = text("""
                SELECT s.id, s.name, s.description, s.status, s.created_at, s.updated_at,
                       s.tags, s.total_return, s.sharpe_ratio
                FROM strategies s
                WHERE s.status != 'ARCHIVED'
                ORDER BY s.updated_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = await session.execute(query, {"limit": limit, "offset": offset})
            rows = result.fetchall()
            
            return [
                {
                    "strategy_id": str(row.id),
                    "source": "ai_ml",
                    "name": row.name,
                    "description": row.description,
                    "status": row.status,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "tags": row.tags or [],
                    "performance": {
                        "total_return": float(row.total_return) if row.total_return else None,
                        "sharpe_ratio": float(row.sharpe_ratio) if row.sharpe_ratio else None
                    }
                }
                for row in rows
            ]
    
    async def _list_no_code_strategies(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """List strategies from No-Code service."""
        async with self.no_code_session_maker() as session:
            query = text("""
                SELECT nw.uuid, nw.name, nw.description, nw.deployment_status as status,
                       nw.created_at, nw.updated_at, nw.tags, nw.category, nw.version
                FROM nocode_workflows nw
                WHERE nw.compilation_status = 'success' 
                AND nw.generated_code IS NOT NULL
                ORDER BY nw.updated_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = await session.execute(query, {"limit": limit, "offset": offset})
            rows = result.fetchall()
            
            return [
                {
                    "strategy_id": str(row.uuid),
                    "source": "no_code",
                    "name": row.name,
                    "description": row.description,
                    "status": row.status,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "tags": row.tags or [],
                    "category": row.category,
                    "version": f"v{row.version}"
                }
                for row in rows
            ]
    
    async def _get_ai_ml_metadata(self, strategy_id: str) -> Dict[str, Any]:
        """Get AI/ML strategy metadata."""
        # Implementation similar to _list_ai_ml_strategies but for single strategy
        pass
    
    async def _get_no_code_metadata(self, strategy_id: str) -> Dict[str, Any]:
        """Get No-Code strategy metadata."""
        # Implementation similar to _list_no_code_strategies but for single strategy
        pass
    
    async def _test_connections(self) -> None:
        """Test database connections."""
        try:
            # Test AI/ML connection
            async with self.ai_ml_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            # Test No-Code connection
            async with self.no_code_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                
        except Exception as e:
            raise DatabaseConnectionError(f"Database connection test failed: {e}")
    
    def _is_cached_and_valid(self, cache_key: str) -> bool:
        """Check if strategy is cached and still valid."""
        if cache_key not in self._strategy_cache:
            return False
            
        cached_at = self._cache_timestamps.get(cache_key)
        if not cached_at:
            return False
            
        age_seconds = (datetime.utcnow() - cached_at).total_seconds()
        return age_seconds < self.cache_ttl_seconds
    
    def _cache_strategy(self, cache_key: str, strategy: StrategyPackage) -> None:
        """Cache a loaded strategy."""
        # Implement LRU eviction if cache is full
        if len(self._strategy_cache) >= self.max_cache_size:
            oldest_key = min(self._cache_timestamps.keys(), 
                           key=lambda k: self._cache_timestamps[k])
            self._strategy_cache.pop(oldest_key)
            self._cache_timestamps.pop(oldest_key)
        
        self._strategy_cache[cache_key] = strategy
        self._cache_timestamps[cache_key] = datetime.utcnow()
    
    def _calculate_checksum(self, content: str) -> str:
        """Calculate SHA-256 checksum of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()