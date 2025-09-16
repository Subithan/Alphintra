"""
Strategy execution sandbox for safe and isolated strategy execution.
"""

import asyncio
import ast
import sys
import os
import tempfile
import shutil
import subprocess
import time
import importlib.util
import traceback
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

import structlog
import pandas as pd
import numpy as np

from app.models.strategies import StrategyPackage
from app.models.signals import TradingSignal, SignalAction, ExecutionParams
from app.models.market_data import OHLCV

logger = structlog.get_logger(__name__)


class SandboxError(Exception):
    """Sandbox execution error."""
    pass


class StrategySandbox:
    """Isolated execution environment for trading strategies."""
    
    def __init__(self, strategy_package: StrategyPackage):
        self.strategy_package = strategy_package
        self.temp_dir: Optional[str] = None
        self.venv_dir: Optional[str] = None
        self.strategy_module = None
        self.strategy_instance = None
        
        # Security restrictions
        self.allowed_imports = {
            'pandas', 'numpy', 'ta', 'datetime', 'math', 'statistics',
            'json', 'typing', 'dataclasses', 'enum', 'decimal',
            'sklearn', 'scipy', 'matplotlib', 'seaborn'
        }
        
        # Blocked dangerous modules/functions
        self.blocked_imports = {
            'os', 'sys', 'subprocess', 'importlib', 'exec', 'eval',
            'open', 'file', 'input', '__import__', 'globals', 'locals',
            'socket', 'urllib', 'requests', 'http', 'ftplib', 'smtplib'
        }
        
        # Execution limits
        self.max_execution_time = 30  # seconds
        self.max_memory_mb = 256
        
    async def initialize(self) -> None:
        """Initialize the sandbox environment."""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="strategy_sandbox_")
            logger.debug("Created sandbox directory", path=self.temp_dir)
            
            # Write strategy files to temp directory
            await self._write_strategy_files()
            
            # Validate strategy code
            await self._validate_strategy_code()
            
            # Setup virtual environment if needed
            if self.strategy_package.requirements:
                await self._setup_virtual_environment()
            
            # Load strategy module
            await self._load_strategy_module()
            
            logger.info("Strategy sandbox initialized successfully",
                       strategy_id=self.strategy_package.strategy_id)
            
        except Exception as e:
            await self.cleanup()
            raise SandboxError(f"Failed to initialize sandbox: {e}")
    
    async def cleanup(self) -> None:
        """Clean up sandbox resources."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.debug("Cleaned up sandbox directory", path=self.temp_dir)
            
            self.strategy_module = None
            self.strategy_instance = None
            
        except Exception as e:
            logger.error("Error cleaning up sandbox", error=str(e))
    
    async def execute_strategy(self, market_data: Dict[str, List[OHLCV]], 
                             parameters: Dict[str, Any]) -> List[TradingSignal]:
        """
        Execute strategy with market data and return signals.
        
        Args:
            market_data: Dictionary mapping symbols to OHLCV data
            parameters: Strategy parameters
            
        Returns:
            List of generated trading signals
        """
        try:
            start_time = time.time()
            
            # Convert market data to pandas DataFrames
            df_data = self._prepare_market_data(market_data)
            
            # Execute strategy with timeout
            signals = await asyncio.wait_for(
                self._run_strategy_logic(df_data, parameters),
                timeout=self.max_execution_time
            )
            
            execution_time = time.time() - start_time
            logger.debug("Strategy executed successfully",
                        strategy_id=self.strategy_package.strategy_id,
                        execution_time=execution_time,
                        signals_count=len(signals) if signals else 0)
            
            return signals or []
            
        except asyncio.TimeoutError:
            raise SandboxError(f"Strategy execution timeout ({self.max_execution_time}s)")
        except Exception as e:
            raise SandboxError(f"Strategy execution failed: {e}")
    
    async def _write_strategy_files(self) -> None:
        """Write strategy files to temporary directory."""
        for filename, file_obj in self.strategy_package.files.items():
            file_path = os.path.join(self.temp_dir, filename)
            
            # Create subdirectories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding=file_obj.encoding) as f:
                f.write(file_obj.content)
            
            logger.debug("Wrote strategy file", filename=filename, path=file_path)
    
    async def _validate_strategy_code(self) -> None:
        """Validate strategy code for security and syntax."""
        main_file_path = os.path.join(self.temp_dir, self.strategy_package.main_file)
        
        try:
            # Read and parse the main strategy file
            with open(main_file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            # Parse AST for static analysis
            tree = ast.parse(code_content)
            
            # Check for dangerous imports and functions
            self._check_ast_security(tree)
            
            logger.debug("Strategy code validation passed",
                        strategy_id=self.strategy_package.strategy_id)
            
        except SyntaxError as e:
            raise SandboxError(f"Strategy syntax error: {e}")
        except Exception as e:
            raise SandboxError(f"Strategy validation failed: {e}")
    
    def _check_ast_security(self, tree: ast.AST) -> None:
        """Check AST for security violations."""
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.blocked_imports:
                            raise SandboxError(f"Blocked import: {alias.name}")
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.blocked_imports:
                        raise SandboxError(f"Blocked import: {node.module}")
            
            # Check function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.blocked_imports:
                        raise SandboxError(f"Blocked function call: {node.func.id}")
    
    async def _setup_virtual_environment(self) -> None:
        """Set up virtual environment with required packages."""
        try:
            self.venv_dir = os.path.join(self.temp_dir, "venv")
            
            # Create virtual environment
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "venv", self.venv_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise SandboxError(f"Failed to create virtual environment: {stderr.decode()}")
            
            # Install requirements
            if self.strategy_package.requirements:
                pip_path = os.path.join(self.venv_dir, "bin", "pip")
                if not os.path.exists(pip_path):  # Windows
                    pip_path = os.path.join(self.venv_dir, "Scripts", "pip.exe")
                
                # Filter and validate requirements
                safe_requirements = self._filter_safe_requirements(
                    self.strategy_package.requirements
                )
                
                if safe_requirements:
                    process = await asyncio.create_subprocess_exec(
                        pip_path, "install", "--no-cache-dir", "--timeout", "60",
                        *safe_requirements,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        logger.warning("Some packages failed to install",
                                     error=stderr.decode()[:500])
            
            logger.debug("Virtual environment setup completed")
            
        except Exception as e:
            raise SandboxError(f"Failed to setup virtual environment: {e}")
    
    def _filter_safe_requirements(self, requirements: List[str]) -> List[str]:
        """Filter requirements to only allow safe packages."""
        safe_packages = {
            'pandas', 'numpy', 'scipy', 'scikit-learn', 'ta', 'matplotlib',
            'seaborn', 'plotly', 'yfinance', 'ccxt', 'python-dateutil'
        }
        
        safe_requirements = []
        for req in requirements:
            # Parse requirement (handle version specifiers)
            package_name = req.split('==')[0].split('>=')[0].split('<=')[0].split('<')[0].split('>')[0]
            package_name = package_name.strip()
            
            if package_name.lower() in safe_packages:
                safe_requirements.append(req)
            else:
                logger.warning("Blocked unsafe package requirement", package=package_name)
        
        return safe_requirements
    
    async def _load_strategy_module(self) -> None:
        """Load the strategy module dynamically."""
        try:
            main_file_path = os.path.join(self.temp_dir, self.strategy_package.main_file)
            
            # Add temp directory to Python path temporarily
            sys.path.insert(0, self.temp_dir)
            
            try:
                # Load module dynamically
                spec = importlib.util.spec_from_file_location(
                    "strategy_module", main_file_path
                )
                self.strategy_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.strategy_module)
                
                # Look for strategy class or function
                strategy_class = self._find_strategy_class()
                if strategy_class:
                    self.strategy_instance = strategy_class()
                
                logger.debug("Strategy module loaded successfully")
                
            finally:
                # Remove temp directory from Python path
                sys.path.remove(self.temp_dir)
            
        except Exception as e:
            raise SandboxError(f"Failed to load strategy module: {e}")
    
    def _find_strategy_class(self):
        """Find the main strategy class in the module."""
        # Look for common strategy class names
        strategy_names = ['Strategy', 'TradingStrategy', 'MyStrategy']
        
        for name in strategy_names:
            if hasattr(self.strategy_module, name):
                cls = getattr(self.strategy_module, name)
                if callable(cls):
                    return cls
        
        # Look for any class that might be a strategy
        for name in dir(self.strategy_module):
            if not name.startswith('_'):
                obj = getattr(self.strategy_module, name)
                if isinstance(obj, type) and hasattr(obj, 'generate_signal'):
                    return obj
        
        return None
    
    def _prepare_market_data(self, market_data: Dict[str, List[OHLCV]]) -> Dict[str, pd.DataFrame]:
        """Convert OHLCV data to pandas DataFrames."""
        df_data = {}
        
        for symbol, ohlcv_list in market_data.items():
            if not ohlcv_list:
                continue
            
            # Convert to DataFrame
            data_rows = []
            for ohlcv in ohlcv_list:
                data_rows.append({
                    'timestamp': ohlcv.timestamp,
                    'open': ohlcv.open_price,
                    'high': ohlcv.high_price,
                    'low': ohlcv.low_price,
                    'close': ohlcv.close_price,
                    'volume': ohlcv.volume
                })
            
            df = pd.DataFrame(data_rows)
            df = df.set_index('timestamp').sort_index()
            df_data[symbol] = df
        
        return df_data
    
    async def _run_strategy_logic(self, df_data: Dict[str, pd.DataFrame],
                                parameters: Dict[str, Any]) -> List[TradingSignal]:
        """Run the actual strategy logic."""
        signals = []
        
        try:
            if self.strategy_instance:
                # Call strategy method
                if hasattr(self.strategy_instance, 'generate_signals'):
                    result = self.strategy_instance.generate_signals(df_data, parameters)
                elif hasattr(self.strategy_instance, 'generate_signal'):
                    result = self.strategy_instance.generate_signal(df_data, parameters)
                else:
                    raise SandboxError("Strategy class must have generate_signal or generate_signals method")
            
            elif hasattr(self.strategy_module, 'generate_signals'):
                result = self.strategy_module.generate_signals(df_data, parameters)
            elif hasattr(self.strategy_module, 'generate_signal'):
                result = self.strategy_module.generate_signal(df_data, parameters)
            else:
                raise SandboxError("Strategy must have generate_signal or generate_signals function")
            
            # Convert result to TradingSignal objects
            if result:
                signals = self._convert_to_trading_signals(result)
            
        except Exception as e:
            logger.error("Error executing strategy logic", error=str(e), traceback=traceback.format_exc())
            raise SandboxError(f"Strategy logic error: {e}")
        
        return signals
    
    def _convert_to_trading_signals(self, result: Any) -> List[TradingSignal]:
        """Convert strategy result to TradingSignal objects."""
        signals = []
        
        try:
            # Handle different result formats
            if isinstance(result, dict):
                # Single signal as dictionary
                signals.append(self._dict_to_signal(result))
                
            elif isinstance(result, list):
                # Multiple signals
                for item in result:
                    if isinstance(item, dict):
                        signals.append(self._dict_to_signal(item))
                    elif isinstance(item, TradingSignal):
                        signals.append(item)
            
            elif isinstance(result, TradingSignal):
                # Already a TradingSignal
                signals.append(result)
            
        except Exception as e:
            logger.error("Error converting strategy result to signals", error=str(e))
        
        return signals
    
    def _dict_to_signal(self, signal_dict: Dict[str, Any]) -> TradingSignal:
        """Convert dictionary to TradingSignal."""
        # Extract required fields
        symbol = signal_dict.get('symbol', 'BTCUSDT')
        action_str = signal_dict.get('action', 'HOLD').upper()
        
        # Convert action string to enum
        try:
            action = SignalAction(action_str)
        except ValueError:
            action = SignalAction.HOLD
        
        confidence = float(signal_dict.get('confidence', 0.5))
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
        # Extract execution parameters
        execution_params = ExecutionParams(
            quantity=float(signal_dict.get('quantity', 0.1)),
            price_target=signal_dict.get('price_target'),
            stop_loss=signal_dict.get('stop_loss'),
            take_profit=signal_dict.get('take_profit')
        )
        
        return TradingSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            execution_params=execution_params,
            risk_score=float(signal_dict.get('risk_score', 0.3)),
            current_price=signal_dict.get('current_price'),
            metadata=signal_dict.get('metadata', {})
        )