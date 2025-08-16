"""
Data ingestion service for automated data collection from various sources.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
import json
import os
import pandas as pd
import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.dataset import (
    Dataset, DataIngestionJob, DataSource, DatasetStatus, 
    DataFormat, DataFrequency, AssetClass
)
from app.core.config import get_settings


class DataSourceConnector:
    """Base class for data source connectors."""
    
    def __init__(self, source_name: str, config: Dict[str, Any]):
        self.source_name = source_name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{source_name}")
    
    async def collect_data(self, symbols: List[str], frequency: DataFrequency, 
                          start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Collect data from the source."""
        raise NotImplementedError("Subclasses must implement collect_data")
    
    async def validate_symbols(self, symbols: List[str]) -> Tuple[List[str], List[str]]:
        """Validate symbols and return valid and invalid lists."""
        raise NotImplementedError("Subclasses must implement validate_symbols")
    
    def get_supported_frequencies(self) -> List[DataFrequency]:
        """Get supported frequencies for this source."""
        raise NotImplementedError("Subclasses must implement get_supported_frequencies")


class BinanceConnector(DataSourceConnector):
    """Connector for Binance cryptocurrency data."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("binance", config)
        self.base_url = "https://api.binance.com"
        
    async def collect_data(self, symbols: List[str], frequency: DataFrequency, 
                          start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Collect data from Binance API."""
        try:
            # Convert frequency to Binance format
            interval_map = {
                DataFrequency.MINUTE_1: "1m",
                DataFrequency.MINUTE_5: "5m",
                DataFrequency.MINUTE_15: "15m",
                DataFrequency.MINUTE_30: "30m",
                DataFrequency.HOUR_1: "1h",
                DataFrequency.HOUR_4: "4h",
                DataFrequency.DAY_1: "1d",
                DataFrequency.WEEK_1: "1w",
                DataFrequency.MONTH_1: "1M"
            }
            
            interval = interval_map.get(frequency)
            if not interval:
                raise ValueError(f"Unsupported frequency: {frequency}")
            
            all_data = []
            
            for symbol in symbols:
                self.logger.info(f"Collecting data for {symbol}")
                
                # Mock data collection (in production, use actual Binance API)
                symbol_data = await self._fetch_symbol_data(symbol, interval, start_date, end_date)
                symbol_data['symbol'] = symbol
                all_data.append(symbol_data)
            
            if not all_data:
                return pd.DataFrame()
            
            # Combine all symbol data
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Sort by timestamp and symbol
            combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
            combined_df = combined_df.sort_values(['timestamp', 'symbol']).reset_index(drop=True)
            
            self.logger.info(f"Collected {len(combined_df)} records for {len(symbols)} symbols")
            return combined_df
            
        except Exception as e:
            self.logger.error(f"Failed to collect Binance data: {str(e)}")
            raise
    
    async def _fetch_symbol_data(self, symbol: str, interval: str, 
                                start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch data for a single symbol (mock implementation)."""
        # In production, this would make actual API calls to Binance
        # For now, generate sample data
        
        # Calculate number of periods
        freq_minutes = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "1d": 1440, "1w": 10080, "1M": 43200
        }
        
        minutes = freq_minutes.get(interval, 60)
        total_minutes = int((end_date - start_date).total_seconds() / 60)
        periods = min(total_minutes // minutes, 1000)  # Limit to 1000 records
        
        # Generate timestamp range
        timestamps = pd.date_range(start=start_date, periods=periods, freq=f"{minutes}T")
        
        # Generate sample OHLCV data
        np.random.seed(hash(symbol) % 2**32)  # Consistent data per symbol
        base_price = np.random.uniform(100, 50000)  # Random base price
        
        # Generate price data with random walk
        returns = np.random.normal(0, 0.02, periods)  # 2% volatility
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        prices = np.array(prices)
        
        # Generate OHLCV data
        data = []
        for i, ts in enumerate(timestamps):
            open_price = prices[i]
            high_price = open_price * (1 + abs(np.random.normal(0, 0.01)))
            low_price = open_price * (1 - abs(np.random.normal(0, 0.01)))
            close_price = prices[i] if i == len(prices) - 1 else prices[i + 1]
            volume = np.random.uniform(1000, 10000)
            
            data.append({
                'timestamp': ts,
                'open': round(open_price, 6),
                'high': round(max(open_price, high_price, close_price), 6),
                'low': round(min(open_price, low_price, close_price), 6),
                'close': round(close_price, 6),
                'volume': round(volume, 2)
            })
        
        return pd.DataFrame(data)
    
    async def validate_symbols(self, symbols: List[str]) -> Tuple[List[str], List[str]]:
        """Validate Binance symbols."""
        # Mock validation - in production, check against Binance exchange info
        valid_symbols = []
        invalid_symbols = []
        
        common_symbols = {
            'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 'XRPUSDT',
            'SOLUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'SHIBUSDT'
        }
        
        for symbol in symbols:
            if symbol.upper() in common_symbols or symbol.upper().endswith('USDT'):
                valid_symbols.append(symbol.upper())
            else:
                invalid_symbols.append(symbol)
        
        return valid_symbols, invalid_symbols
    
    def get_supported_frequencies(self) -> List[DataFrequency]:
        """Get supported frequencies for Binance."""
        return [
            DataFrequency.MINUTE_1,
            DataFrequency.MINUTE_5,
            DataFrequency.MINUTE_15,
            DataFrequency.MINUTE_30,
            DataFrequency.HOUR_1,
            DataFrequency.HOUR_4,
            DataFrequency.DAY_1,
            DataFrequency.WEEK_1,
            DataFrequency.MONTH_1
        ]


class YahooFinanceConnector(DataSourceConnector):
    """Connector for Yahoo Finance stock data."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("yahoo_finance", config)
    
    async def collect_data(self, symbols: List[str], frequency: DataFrequency, 
                          start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Collect data from Yahoo Finance."""
        try:
            # Only support daily data for now
            if frequency != DataFrequency.DAY_1:
                raise ValueError("Yahoo Finance connector only supports daily data")
            
            all_data = []
            
            for symbol in symbols:
                self.logger.info(f"Collecting data for {symbol}")
                symbol_data = await self._fetch_symbol_data(symbol, start_date, end_date)
                symbol_data['symbol'] = symbol
                all_data.append(symbol_data)
            
            if not all_data:
                return pd.DataFrame()
            
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
            combined_df = combined_df.sort_values(['timestamp', 'symbol']).reset_index(drop=True)
            
            return combined_df
            
        except Exception as e:
            self.logger.error(f"Failed to collect Yahoo Finance data: {str(e)}")
            raise
    
    async def _fetch_symbol_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch stock data (mock implementation)."""
        # Generate sample stock data
        days = (end_date - start_date).days
        periods = min(days, 1000)  # Limit to 1000 days
        
        timestamps = pd.date_range(start=start_date, periods=periods, freq='D')
        
        # Generate realistic stock price data
        np.random.seed(hash(symbol) % 2**32)
        base_price = np.random.uniform(50, 500)
        
        returns = np.random.normal(0.001, 0.02, periods)  # Slight upward bias
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(max(0.01, prices[-1] * (1 + ret)))  # Prevent negative prices
        
        prices = np.array(prices)
        
        data = []
        for i, ts in enumerate(timestamps):
            open_price = prices[i]
            close_price = prices[i] if i == len(prices) - 1 else prices[i + 1]
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
            volume = int(np.random.uniform(100000, 1000000))
            
            data.append({
                'timestamp': ts,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2), 
                'close': round(close_price, 2),
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    async def validate_symbols(self, symbols: List[str]) -> Tuple[List[str], List[str]]:
        """Validate Yahoo Finance symbols."""
        valid_symbols = []
        invalid_symbols = []
        
        # Common stock symbols
        common_symbols = {
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA',
            'NFLX', 'BABA', 'V', 'JPM', 'JNJ', 'WMT', 'PG', 'UNH'
        }
        
        for symbol in symbols:
            if symbol.upper() in common_symbols or len(symbol) <= 5:
                valid_symbols.append(symbol.upper())
            else:
                invalid_symbols.append(symbol)
        
        return valid_symbols, invalid_symbols
    
    def get_supported_frequencies(self) -> List[DataFrequency]:
        """Get supported frequencies for Yahoo Finance."""
        return [DataFrequency.DAY_1]


class DataIngestionService:
    """Service for managing data ingestion jobs and collecting data."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # Initialize connectors
        self.connectors = {
            "binance": BinanceConnector({}),
            "yahoo_finance": YahooFinanceConnector({}),
        }
    
    async def create_ingestion_job(self, job_data: Dict[str, Any], 
                                 user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Create a new data ingestion job."""
        try:
            # Validate data source
            data_source = job_data.get("data_source")
            if data_source not in self.connectors:
                return {
                    "success": False,
                    "error": f"Unsupported data source: {data_source}"
                }
            
            connector = self.connectors[data_source]
            
            # Validate frequency
            frequency = DataFrequency(job_data.get("frequency"))
            if frequency not in connector.get_supported_frequencies():
                return {
                    "success": False,
                    "error": f"Frequency {frequency.value} not supported by {data_source}"
                }
            
            # Validate symbols
            symbols = job_data.get("symbols", [])
            valid_symbols, invalid_symbols = await connector.validate_symbols(symbols)
            
            if not valid_symbols:
                return {
                    "success": False,
                    "error": "No valid symbols provided",
                    "invalid_symbols": invalid_symbols
                }
            
            # Create ingestion job
            job = DataIngestionJob(
                user_id=UUID(user_id),
                job_name=job_data["job_name"],
                data_source=data_source,
                symbols=valid_symbols,
                frequency=frequency,
                start_date=datetime.fromisoformat(job_data["start_date"]),
                end_date=datetime.fromisoformat(job_data["end_date"]),
                is_recurring=job_data.get("is_recurring", False),
                schedule_cron=job_data.get("schedule_cron"),
                ingestion_config=job_data.get("ingestion_config", {}),
                quality_checks=job_data.get("quality_checks", [])
            )
            
            db.add(job)
            await db.commit()
            await db.refresh(job)
            
            result = {
                "success": True,
                "job_id": str(job.id),
                "valid_symbols": valid_symbols
            }
            
            if invalid_symbols:
                result["invalid_symbols"] = invalid_symbols
                result["warning"] = f"Some symbols were invalid: {invalid_symbols}"
            
            self.logger.info(f"Created ingestion job {job.id} for user {user_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create ingestion job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def execute_ingestion_job(self, job_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Execute a data ingestion job."""
        try:
            # Get job
            result = await db.execute(
                select(DataIngestionJob).where(DataIngestionJob.id == UUID(job_id))
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return {"success": False, "error": "Job not found"}
            
            if job.status == "running":
                return {"success": False, "error": "Job is already running"}
            
            # Update job status
            job.status = "running"
            job.start_time = datetime.utcnow()
            job.retry_count += 1
            await db.commit()
            
            try:
                # Get connector
                connector = self.connectors[job.data_source]
                
                # Collect data
                self.logger.info(f"Starting data collection for job {job_id}")
                df = await connector.collect_data(
                    symbols=job.symbols,
                    frequency=job.frequency,
                    start_date=job.start_date,
                    end_date=job.end_date
                )
                
                if df.empty:
                    raise ValueError("No data collected")
                
                # Store data as dataset
                dataset_id = await self._store_as_dataset(df, job, db)
                
                # Update job with results
                job.status = "completed"
                job.end_time = datetime.utcnow()
                job.duration = (job.end_time - job.start_time).total_seconds()
                job.created_dataset_id = UUID(dataset_id)
                job.records_collected = len(df)
                job.bytes_processed = df.memory_usage(deep=True).sum()
                job.logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "INFO",
                    "message": f"Successfully collected {len(df)} records"
                })
                
                await db.commit()
                
                self.logger.info(f"Completed ingestion job {job_id}, created dataset {dataset_id}")
                
                return {
                    "success": True,
                    "dataset_id": dataset_id,
                    "records_collected": len(df),
                    "execution_time": job.duration
                }
                
            except Exception as e:
                # Update job with error
                job.status = "failed"
                job.end_time = datetime.utcnow()
                job.duration = (job.end_time - job.start_time).total_seconds() if job.start_time else 0
                job.error_message = str(e)
                job.logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "ERROR", 
                    "message": str(e)
                })
                
                await db.commit()
                raise
                
        except Exception as e:
            self.logger.error(f"Failed to execute ingestion job {job_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _store_as_dataset(self, df: pd.DataFrame, job: DataIngestionJob, 
                               db: AsyncSession) -> str:
        """Store collected data as a dataset."""
        try:
            # Generate file path
            dataset_id = str(uuid4())
            filename = f"ingested_data_{dataset_id}.parquet"
            storage_dir = os.path.join(self.settings.DATA_STORAGE_PATH, "ingested")
            os.makedirs(storage_dir, exist_ok=True)
            file_path = os.path.join(storage_dir, filename)
            
            # Save data to parquet
            df.to_parquet(file_path, index=False)
            file_size = os.path.getsize(file_path)
            
            # Calculate content hash
            with open(file_path, 'rb') as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Determine asset class
            asset_class = AssetClass.CRYPTO if job.data_source == "binance" else AssetClass.STOCKS
            
            # Create dataset record
            dataset = Dataset(
                id=UUID(dataset_id),
                user_id=job.user_id,
                name=f"{job.job_name} - {job.data_source.title()} Data",
                description=f"Data ingested from {job.data_source} for symbols: {', '.join(job.symbols)}",
                source=DataSource.EXTERNAL,
                asset_class=asset_class,
                symbols=job.symbols,
                frequency=job.frequency,
                start_date=job.start_date,
                end_date=job.end_date,
                columns=df.columns.tolist(),
                row_count=len(df),
                file_size=file_size,
                data_format=DataFormat.PARQUET,
                status=DatasetStatus.READY,
                is_validated=False,  # Will be validated separately
                file_path=file_path,
                original_filename=filename,
                content_hash=content_hash,
                storage_backend="local",
                compression="snappy",
                data_types={str(col): str(df[col].dtype) for col in df.columns},
                tags=[job.data_source, "ingested", job.frequency.value],
                category="market_data"
            )
            
            db.add(dataset)
            await db.commit()
            
            return dataset_id
            
        except Exception as e:
            self.logger.error(f"Failed to store dataset: {str(e)}")
            raise
    
    async def list_ingestion_jobs(self, filters: Dict[str, Any], 
                                db: AsyncSession) -> List[Dict[str, Any]]:
        """List ingestion jobs with optional filtering."""
        try:
            query = select(DataIngestionJob)
            
            # Apply filters
            if filters.get("user_id"):
                query = query.where(DataIngestionJob.user_id == UUID(filters["user_id"]))
            
            if filters.get("status"):
                query = query.where(DataIngestionJob.status == filters["status"])
            
            if filters.get("data_source"):
                query = query.where(DataIngestionJob.data_source == filters["data_source"])
            
            # Apply sorting
            sort_by = filters.get("sort_by", "created_at")
            sort_order = filters.get("sort_order", "desc")
            
            if sort_by == "job_name":
                order_column = DataIngestionJob.job_name
            elif sort_by == "start_time":
                order_column = DataIngestionJob.start_time
            else:
                order_column = DataIngestionJob.created_at
            
            if sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
            
            # Apply pagination
            limit = filters.get("limit", 50)
            offset = filters.get("offset", 0)
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = await db.execute(query)
            jobs = result.scalars().all()
            
            # Convert to dictionaries
            job_list = []
            for job in jobs:
                job_dict = {
                    "id": str(job.id),
                    "job_name": job.job_name,
                    "data_source": job.data_source,
                    "symbols": job.symbols,
                    "frequency": job.frequency.value,
                    "start_date": job.start_date.isoformat(),
                    "end_date": job.end_date.isoformat(),
                    "status": job.status,
                    "is_recurring": job.is_recurring,
                    "records_collected": job.records_collected,
                    "created_at": job.created_at.isoformat(),
                    "duration": job.duration,
                    "error_message": job.error_message
                }
                
                if job.created_dataset_id:
                    job_dict["created_dataset_id"] = str(job.created_dataset_id)
                
                job_list.append(job_dict)
            
            return job_list
            
        except Exception as e:
            self.logger.error(f"Failed to list ingestion jobs: {str(e)}")
            return []
    
    async def get_ingestion_job(self, job_id: str, user_id: str, 
                              db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get a specific ingestion job."""
        try:
            result = await db.execute(
                select(DataIngestionJob)
                .options(selectinload(DataIngestionJob.created_dataset))
                .where(
                    DataIngestionJob.id == UUID(job_id),
                    DataIngestionJob.user_id == UUID(user_id)
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return None
            
            job_dict = {
                "id": str(job.id),
                "job_name": job.job_name,
                "data_source": job.data_source,
                "symbols": job.symbols,
                "frequency": job.frequency.value,
                "start_date": job.start_date.isoformat(),
                "end_date": job.end_date.isoformat(),
                "status": job.status,
                "is_recurring": job.is_recurring,
                "schedule_cron": job.schedule_cron,
                "records_collected": job.records_collected,
                "bytes_processed": job.bytes_processed,
                "retry_count": job.retry_count,
                "max_retries": job.max_retries,
                "error_message": job.error_message,
                "logs": job.logs,
                "ingestion_config": job.ingestion_config,
                "quality_checks": job.quality_checks,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "start_time": job.start_time.isoformat() if job.start_time else None,
                "end_time": job.end_time.isoformat() if job.end_time else None,
                "duration": job.duration
            }
            
            if job.created_dataset:
                job_dict["created_dataset"] = {
                    "id": str(job.created_dataset.id),
                    "name": job.created_dataset.name,
                    "status": job.created_dataset.status.value,
                    "row_count": job.created_dataset.row_count
                }
            
            return job_dict
            
        except Exception as e:
            self.logger.error(f"Failed to get ingestion job: {str(e)}")
            return None
    
    async def cancel_ingestion_job(self, job_id: str, user_id: str, 
                                 db: AsyncSession) -> Dict[str, Any]:
        """Cancel a running ingestion job."""
        try:
            result = await db.execute(
                select(DataIngestionJob).where(
                    DataIngestionJob.id == UUID(job_id),
                    DataIngestionJob.user_id == UUID(user_id)
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return {"success": False, "error": "Job not found"}
            
            if job.status not in ["pending", "running"]:
                return {"success": False, "error": "Job cannot be cancelled"}
            
            # Update job status
            job.status = "cancelled"
            job.end_time = datetime.utcnow()
            if job.start_time:
                job.duration = (job.end_time - job.start_time).total_seconds()
            job.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Job cancelled by user"
            })
            
            await db.commit()
            
            self.logger.info(f"Cancelled ingestion job {job_id}")
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Failed to cancel ingestion job: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_supported_sources(self) -> Dict[str, Any]:
        """Get information about supported data sources."""
        sources = {}
        
        for name, connector in self.connectors.items():
            sources[name] = {
                "name": name.replace("_", " ").title(),
                "supported_frequencies": [f.value for f in connector.get_supported_frequencies()],
                "description": f"Data connector for {name.replace('_', ' ').title()}"
            }
        
        return sources