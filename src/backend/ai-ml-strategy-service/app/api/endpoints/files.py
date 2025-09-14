"""
File Management API endpoints for IDE integration.

This module handles file operations for the IDE including:
- File creation, reading, updating, deletion
- Project management
- File system operations for strategy development
"""

import os
import shutil
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import asyncio
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Body, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/files", tags=["File Management"])

# Configuration
BASE_PROJECT_DIR = Path("/tmp/alphintra_projects")  # Can be configured via environment
ALLOWED_EXTENSIONS = {".py", ".md", ".json", ".txt", ".yaml", ".yml", ".sql", ".js", ".ts", ".html", ".css"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# Pydantic models
class FileInfo(BaseModel):
    id: str
    name: str
    path: str
    content: Optional[str] = None
    language: str
    size: int = 0
    modified: bool = False
    created_at: datetime
    updated_at: datetime
    is_directory: bool = False


class ProjectInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    path: str
    files: List[FileInfo] = []
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any] = Field(default_factory=dict)


class CreateFileRequest(BaseModel):
    name: str
    content: str = ""
    language: str = "python"
    project_id: Optional[str] = None


class UpdateFileRequest(BaseModel):
    content: str
    language: Optional[str] = None


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    template: Optional[str] = None  # basic, ml, trading, etc.


# Helper functions
def get_language_from_extension(filename: str) -> str:
    """Determine programming language from file extension."""
    ext = Path(filename).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.md': 'markdown',
        '.sql': 'sql',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.txt': 'plaintext'
    }
    return language_map.get(ext, 'plaintext')


def generate_file_id(project_id: str, filename: str) -> str:
    """Generate unique file ID."""
    return f"{project_id}_{filename}_{int(datetime.now().timestamp())}"


def validate_filename(filename: str) -> bool:
    """Validate filename for security."""
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        return False
    
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def get_project_path(project_id: str) -> Path:
    """Get full path for project directory."""
    return BASE_PROJECT_DIR / project_id


def ensure_project_dir(project_id: str) -> Path:
    """Ensure project directory exists."""
    project_path = get_project_path(project_id)
    project_path.mkdir(parents=True, exist_ok=True)
    return project_path


def file_to_info(file_path: Path, project_id: str, content: bool = False) -> FileInfo:
    """Convert file path to FileInfo object."""
    stat = file_path.stat()
    relative_path = file_path.relative_to(get_project_path(project_id))
    
    file_content = None
    if content and file_path.is_file():
        try:
            file_content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Could not read file content: {e}")
            file_content = ""

    return FileInfo(
        id=generate_file_id(project_id, file_path.name),
        name=file_path.name,
        path=f"/{relative_path}",
        content=file_content,
        language=get_language_from_extension(file_path.name),
        size=stat.st_size if file_path.is_file() else 0,
        modified=False,
        created_at=datetime.fromtimestamp(stat.st_ctime),
        updated_at=datetime.fromtimestamp(stat.st_mtime),
        is_directory=file_path.is_dir()
    )


# Project endpoints
@router.post("/projects", response_model=ProjectInfo, status_code=status.HTTP_201_CREATED)
async def create_project(request: CreateProjectRequest):
    """Create a new project with optional template."""
    try:
        project_id = f"project_{int(datetime.now().timestamp())}"
        project_path = ensure_project_dir(project_id)
        
        # Create project metadata
        metadata = {
            "id": project_id,
            "name": request.name,
            "description": request.description,
            "created_at": datetime.now().isoformat(),
            "settings": {
                "aiEnabled": True,
                "suggestions": True,
                "autoComplete": True,
                "errorDetection": True,
                "testGeneration": True
            }
        }
        
        # Save metadata
        metadata_file = project_path / ".project.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        
        # Create template files based on template type
        if request.template == "trading":
            template_content = '''# AI-powered trading strategy
# Generated from trading template

import pandas as pd
import numpy as np
from typing import Dict, List
from app.sdk.strategy import BaseStrategy
from app.sdk.indicators import TechnicalIndicators
from app.sdk.orders import OrderManager
from app.sdk.risk import RiskManager

class TradingStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "{}"
        self.indicators = TechnicalIndicators()
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        
    def initialize(self):
        """Initialize strategy parameters."""
        self.lookback_period = 20
        self.risk_per_trade = 0.02
        
    def on_data(self, data: pd.DataFrame) -> Dict:
        """Process market data and generate signals."""
        # Calculate technical indicators
        data['sma_20'] = self.indicators.sma(data['close'], 20)
        data['rsi'] = self.indicators.rsi(data['close'], 14)
        
        # Generate signals
        signal = self.generate_signal(data.iloc[-1])
        
        # Apply risk management
        position_size = self.risk_manager.calculate_position_size(
            account_balance=self.get_account_balance(),
            risk_per_trade=self.risk_per_trade,
            entry_price=data['close'].iloc[-1],
            stop_loss_price=data['close'].iloc[-1] * 0.98
        )
        
        return {{
            'signal': signal,
            'position_size': position_size,
            'timestamp': data.index[-1]
        }}
        
    def generate_signal(self, latest_data) -> str:
        """Generate buy/sell/hold signal based on indicators."""
        if latest_data['rsi'] < 30 and latest_data['close'] > latest_data['sma_20']:
            return 'BUY'
        elif latest_data['rsi'] > 70:
            return 'SELL'
        else:
            return 'HOLD'
            
    def on_signal(self, signal_data: Dict):
        """Execute trades based on signals."""
        if signal_data['signal'] == 'BUY':
            self.order_manager.place_market_order(
                symbol=self.symbol,
                side='buy',
                quantity=signal_data['position_size']
            )
        elif signal_data['signal'] == 'SELL':
            self.order_manager.place_market_order(
                symbol=self.symbol,
                side='sell',
                quantity=signal_data['position_size']
            )
'''.format(request.name)
        elif request.template == "ml":
            template_content = '''# AI/ML Strategy Template
# Machine learning-based trading strategy

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from app.sdk.strategy import BaseStrategy
from app.sdk.data import DataManager

class MLStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "{}"
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML model."""
        features = pd.DataFrame(index=data.index)
        
        # Technical indicators as features
        features['returns'] = data['close'].pct_change()
        features['sma_5'] = data['close'].rolling(5).mean()
        features['sma_20'] = data['close'].rolling(20).mean()
        features['rsi'] = self.calculate_rsi(data['close'], 14)
        features['volatility'] = data['close'].rolling(20).std()
        
        # Price-based features
        features['price_change'] = data['close'].pct_change()
        features['volume_change'] = data['volume'].pct_change()
        features['high_low_ratio'] = data['high'] / data['low']
        
        return features.dropna()
        
    def train_model(self, data: pd.DataFrame):
        """Train the ML model."""
        features = self.prepare_features(data)
        
        # Create target variable (1 for price increase, 0 for decrease)
        target = (data['close'].shift(-1) > data['close']).astype(int)
        target = target.loc[features.index]
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.model.fit(features_scaled, target)
        self.is_trained = True
        
        print(f"Model trained with {{len(features)}} samples")
        
    def predict_signal(self, data: pd.DataFrame) -> str:
        """Predict trading signal using trained model."""
        if not self.is_trained:
            return 'HOLD'
            
        features = self.prepare_features(data)
        if len(features) == 0:
            return 'HOLD'
            
        # Make prediction
        latest_features = features.iloc[-1:].values
        features_scaled = self.scaler.transform(latest_features)
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0]
        
        # Convert prediction to signal with confidence threshold
        confidence_threshold = 0.6
        if prediction == 1 and probability[1] > confidence_threshold:
            return 'BUY'
        elif prediction == 0 and probability[0] > confidence_threshold:
            return 'SELL'
        else:
            return 'HOLD'
            
    def on_data(self, data: pd.DataFrame) -> Dict:
        """Process data and generate ML-based signals."""
        # Ensure we have enough data
        if len(data) < 50:
            return {{'signal': 'HOLD', 'reason': 'Insufficient data'}}
            
        # Train model if not trained (in real scenario, this would be done separately)
        if not self.is_trained and len(data) > 100:
            self.train_model(data[:-20])  # Leave recent data for prediction
            
        # Generate signal
        signal = self.predict_signal(data)
        
        return {{
            'signal': signal,
            'timestamp': data.index[-1],
            'model_trained': self.is_trained
        }}
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
'''.format(request.name)
        else:
            # Basic template
            template_content = '''# {} Strategy
# Basic strategy template

import pandas as pd
import numpy as np
from typing import Dict, List

class Strategy:
    def __init__(self):
        self.name = "{}"
        
    def initialize(self):
        """Initialize strategy parameters."""
        pass
        
    def on_data(self, data: pd.DataFrame) -> Dict:
        """Process market data and generate signals."""
        # Your trading logic here
        return {{'signal': 'HOLD'}}
        
    def on_signal(self, signal_data: Dict):
        """Execute trades based on signals."""
        pass

# Example usage
if __name__ == "__main__":
    strategy = Strategy()
    strategy.initialize()
    
    # Example data processing
    # data = pd.DataFrame(...)  # Your market data
    # result = strategy.on_data(data)
    # print(result)
'''.format(request.name, request.name)
        
        # Create main strategy file
        main_file = project_path / "main.py"
        main_file.write_text(template_content)
        
        # Create README
        readme_content = f"""# {request.name}

{request.description or 'AI-powered trading strategy project'}

## Overview

This project contains a trading strategy implementation using Alphintra's AI/ML Strategy Service.

## Files

- `main.py` - Main strategy implementation
- `.project.json` - Project metadata and settings

## Getting Started

1. Implement your strategy logic in `main.py`
2. Use the IDE's AI assistant to help develop and optimize your strategy
3. Backtest your strategy using the platform's backtesting engine
4. Deploy to paper trading when ready

## Template Type

Template: {request.template or 'basic'}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        readme_file = project_path / "README.md"
        readme_file.write_text(readme_content)
        
        # Load project info
        project_info = await get_project(project_id)
        
        logger.info(f"Created new project: {project_id} - {request.name}")
        return project_info
        
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/projects", response_model=List[ProjectInfo])
async def list_projects():
    """List all projects."""
    try:
        projects = []
        if BASE_PROJECT_DIR.exists():
            for project_dir in BASE_PROJECT_DIR.iterdir():
                if project_dir.is_dir():
                    try:
                        project_info = await get_project(project_dir.name)
                        projects.append(project_info)
                    except Exception as e:
                        logger.warning(f"Skipping invalid project {project_dir.name}: {e}")
                        continue
        
        return projects
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")


@router.get("/projects/{project_id}", response_model=ProjectInfo)
async def get_project(project_id: str):
    """Get project details with all files."""
    try:
        project_path = get_project_path(project_id)
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Load metadata
        metadata_file = project_path / ".project.json"
        metadata = {"id": project_id, "name": project_id, "created_at": datetime.now().isoformat()}
        
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text())
            except Exception:
                pass
        
        # Get all files
        files = []
        for file_path in project_path.rglob("*"):
            if file_path.name.startswith(".") and file_path.name != ".project.json":
                continue  # Skip hidden files except metadata
            if file_path.is_file():
                files.append(file_to_info(file_path, project_id, content=False))
        
        return ProjectInfo(
            id=project_id,
            name=metadata.get("name", project_id),
            description=metadata.get("description"),
            path=str(project_path),
            files=files,
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.now(),
            settings=metadata.get("settings", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its files."""
    try:
        project_path = get_project_path(project_id)
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        shutil.rmtree(project_path)
        logger.info(f"Deleted project: {project_id}")
        
        return {"message": f"Project {project_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")


# File endpoints
@router.post("/projects/{project_id}/files", response_model=FileInfo, status_code=status.HTTP_201_CREATED)
async def create_file(project_id: str, request: CreateFileRequest):
    """Create a new file in a project."""
    try:
        # Validate filename
        if not validate_filename(request.name):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        project_path = get_project_path(project_id)
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        file_path = project_path / request.name
        if file_path.exists():
            raise HTTPException(status_code=409, detail="File already exists")
        
        # Create file with content
        file_path.write_text(request.content, encoding='utf-8')
        
        logger.info(f"Created file: {project_id}/{request.name}")
        return file_to_info(file_path, project_id, content=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")


@router.get("/projects/{project_id}/files/{filename:path}", response_model=FileInfo)
async def get_file(project_id: str, filename: str):
    """Get file content."""
    try:
        project_path = get_project_path(project_id)
        file_path = project_path / filename
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check - ensure file is within project directory
        try:
            file_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return file_to_info(file_path, project_id, content=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file: {str(e)}")


@router.put("/projects/{project_id}/files/{filename:path}", response_model=FileInfo)
async def update_file(project_id: str, filename: str, request: UpdateFileRequest):
    """Update file content."""
    try:
        project_path = get_project_path(project_id)
        file_path = project_path / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check
        try:
            file_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check file size
        if len(request.content.encode('utf-8')) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Update file
        file_path.write_text(request.content, encoding='utf-8')
        
        logger.info(f"Updated file: {project_id}/{filename}")
        return file_to_info(file_path, project_id, content=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")


@router.delete("/projects/{project_id}/files/{filename:path}")
async def delete_file(project_id: str, filename: str):
    """Delete a file."""
    try:
        project_path = get_project_path(project_id)
        file_path = project_path / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check
        try:
            file_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        file_path.unlink()
        logger.info(f"Deleted file: {project_id}/{filename}")
        
        return {"message": f"File {filename} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


# Utility endpoints
@router.get("/projects/{project_id}/files", response_model=List[FileInfo])
async def list_project_files(project_id: str, include_content: bool = Query(False)):
    """List all files in a project."""
    try:
        project_path = get_project_path(project_id)
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        files = []
        for file_path in project_path.rglob("*"):
            if file_path.name.startswith(".") and file_path.name != ".project.json":
                continue
            if file_path.is_file():
                files.append(file_to_info(file_path, project_id, content=include_content))
        
        return files
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


# Initialize base directory
@router.on_event("startup")
async def startup():
    """Initialize file management system."""
    BASE_PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"File management system initialized at {BASE_PROJECT_DIR}")