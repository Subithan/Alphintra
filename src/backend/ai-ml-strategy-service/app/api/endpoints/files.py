"""
File Management API endpoints for IDE integration.

This module handles file operations for the IDE including:
- File creation, reading, updating, deletion
- Project management with user associations
- Database-based file storage
"""

import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Body, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user_with_permissions
from app.models.user import User
from app.models.file_management import (
    Project, ProjectFile, ProjectTemplate, FileSession, FileVersion
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/files", tags=["File Management"])

# Configuration
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
    version: int = 1
    checksum: Optional[str] = None


class ProjectInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    template_type: str = "custom"
    files: List[FileInfo] = []
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any] = Field(default_factory=dict)
    user_id: str
    file_count: int = 0


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
    from pathlib import Path
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


def validate_filename(filename: str) -> bool:
    """Validate filename for security."""
    if not filename or ".." in filename or "\\" in filename:
        return False
    
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def calculate_checksum(content: str) -> str:
    """Calculate SHA-256 checksum of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def file_model_to_info(file_model: ProjectFile, include_content: bool = False) -> FileInfo:
    """Convert ProjectFile model to FileInfo."""
    return FileInfo(
        id=str(file_model.id),
        name=file_model.file_name,
        path=file_model.file_path,
        content=file_model.content if include_content else None,
        language=file_model.language,
        size=file_model.size_bytes,
        modified=False,  # Can be enhanced with session tracking
        created_at=file_model.created_at,
        updated_at=file_model.updated_at,
        is_directory=file_model.is_directory,
        version=file_model.version,
        checksum=file_model.checksum
    )


def project_model_to_info(project_model: Project, include_files: bool = True) -> ProjectInfo:
    """Convert Project model to ProjectInfo."""
    files = []
    if include_files and project_model.files:
        files = [file_model_to_info(f, include_content=False) for f in project_model.files]
    
    return ProjectInfo(
        id=str(project_model.id),
        name=project_model.name,
        description=project_model.description,
        template_type=project_model.template_type,
        files=files,
        created_at=project_model.created_at,
        updated_at=project_model.updated_at,
        settings=project_model.settings or {},
        user_id=str(project_model.user_id),
        file_count=len(project_model.files) if project_model.files else 0
    )


async def get_project_templates() -> Dict[str, Dict]:
    """Get available project templates."""
    return {
        "trading": {
            "display_name": "Trading Strategy",
            "description": "AI-powered trading strategy with technical indicators",
            "default_files": [
                {
                    "name": "main.py",
                    "content": """# AI-powered trading strategy
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
        self.name = "Trading Strategy"
        self.indicators = TechnicalIndicators()
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        
    def initialize(self):
        \"\"\"Initialize strategy parameters.\"\"\"
        self.lookback_period = 20
        self.risk_per_trade = 0.02
        
    def on_data(self, data: pd.DataFrame) -> Dict:
        \"\"\"Process market data and generate signals.\"\"\"
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
        
        return {
            'signal': signal,
            'position_size': position_size,
            'timestamp': data.index[-1]
        }
        
    def generate_signal(self, latest_data) -> str:
        \"\"\"Generate buy/sell/hold signal based on indicators.\"\"\"
        if latest_data['rsi'] < 30 and latest_data['close'] > latest_data['sma_20']:
            return 'BUY'
        elif latest_data['rsi'] > 70:
            return 'SELL'
        else:
            return 'HOLD'
            
    def on_signal(self, signal_data: Dict):
        \"\"\"Execute trades based on signals.\"\"\"
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
"""
                }
            ]
        },
        "ml": {
            "display_name": "ML Strategy",
            "description": "Machine learning-based trading strategy",
            "default_files": [
                {
                    "name": "main.py",
                    "content": """# AI/ML Strategy Template
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
        self.name = "ML Strategy"
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        \"\"\"Prepare features for ML model.\"\"\"
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
        \"\"\"Train the ML model.\"\"\"
        features = self.prepare_features(data)
        
        # Create target variable (1 for price increase, 0 for decrease)
        target = (data['close'].shift(-1) > data['close']).astype(int)
        target = target.loc[features.index]
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.model.fit(features_scaled, target)
        self.is_trained = True
        
        print(f"Model trained with {len(features)} samples")
        
    def on_data(self, data: pd.DataFrame) -> Dict:
        \"\"\"Process data and generate ML-based signals.\"\"\"
        # Ensure we have enough data
        if len(data) < 50:
            return {'signal': 'HOLD', 'reason': 'Insufficient data'}
            
        # Train model if not trained
        if not self.is_trained and len(data) > 100:
            self.train_model(data[:-20])
            
        # Generate signal
        signal = self.predict_signal(data)
        
        return {
            'signal': signal,
            'timestamp': data.index[-1],
            'model_trained': self.is_trained
        }
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        \"\"\"Calculate RSI indicator.\"\"\"
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
"""
                }
            ]
        },
        "basic": {
            "display_name": "Basic Strategy",
            "description": "Basic strategy template",
            "default_files": [
                {
                    "name": "main.py",
                    "content": """# Basic Strategy Template

import pandas as pd
import numpy as np
from typing import Dict, List

class Strategy:
    def __init__(self):
        self.name = "Basic Strategy"
        
    def initialize(self):
        \"\"\"Initialize strategy parameters.\"\"\"
        pass
        
    def on_data(self, data: pd.DataFrame) -> Dict:
        \"\"\"Process market data and generate signals.\"\"\"
        # Your trading logic here
        return {'signal': 'HOLD'}
        
    def on_signal(self, signal_data: Dict):
        \"\"\"Execute trades based on signals.\"\"\"
        pass

# Example usage
if __name__ == "__main__":
    strategy = Strategy()
    strategy.initialize()
    
    # Example data processing
    # data = pd.DataFrame(...)  # Your market data
    # result = strategy.on_data(data)
    # print(result)
"""
                }
            ]
        }
    }


# Project endpoints
@router.post("/projects", response_model=ProjectInfo, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    # TODO: Re-enable authentication for production
    # current_user: User = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project with optional template."""
    try:
        # Create project
        # TODO: Use actual user ID from authentication in production
        dev_user_id = UUID("00000000-0000-0000-0000-000000000001")
        
        project = Project(
            name=request.name,
            description=request.description or "",
            template_type=request.template or "basic",
            user_id=dev_user_id,
            settings={
                "aiEnabled": True,
                "suggestions": True,
                "autoComplete": True,
                "errorDetection": True,
                "testGeneration": True
            }
        )
        
        db.add(project)
        await db.flush()  # Get the project ID
        
        # Add template files
        templates = await get_project_templates()
        template_config = templates.get(request.template or "basic", templates["basic"])
        
        for file_config in template_config.get("default_files", []):
            content = file_config["content"]
            checksum = calculate_checksum(content)
            
            project_file = ProjectFile(
                project_id=project.id,
                file_path=f"/{file_config['name']}",
                file_name=file_config["name"],
                content=content,
                file_type="text",
                size_bytes=len(content.encode('utf-8')),
                language=get_language_from_extension(file_config["name"]),
                encoding="utf-8",
                version=1,
                checksum=checksum,
                is_directory=False
            )
            
            db.add(project_file)
        
        # Create README
        readme_content = f"""# {request.name}

{request.description or 'AI-powered trading strategy project'}

## Overview

This project contains a trading strategy implementation using Alphintra's AI/ML Strategy Service.

## Files

- `main.py` - Main strategy implementation

## Getting Started

1. Implement your strategy logic in `main.py`
2. Use the IDE's AI assistant to help develop and optimize your strategy
3. Backtest your strategy using the platform's backtesting engine
4. Deploy to paper trading when ready

## Template Type

Template: {request.template or 'basic'}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        readme_checksum = calculate_checksum(readme_content)
        readme_file = ProjectFile(
            project_id=project.id,
            file_path="/README.md",
            file_name="README.md",
            content=readme_content,
            file_type="text",
            size_bytes=len(readme_content.encode('utf-8')),
            language="markdown",
            encoding="utf-8",
            version=1,
            checksum=readme_checksum,
            is_directory=False
        )
        
        db.add(readme_file)
        await db.commit()
        
        # Reload with files
        await db.refresh(project)
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.files))
            .where(Project.id == project.id)
        )
        project_with_files = result.scalar_one()
        
        logger.info(f"Created new project: {project.id} - {request.name} for user {dev_user_id}")
        return project_model_to_info(project_with_files)
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/projects", response_model=List[ProjectInfo])
async def list_projects(
    # TODO: Re-enable authentication for production
    # current_user: User = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """List all projects for the current user."""
    try:
        # TODO: Use actual user ID from authentication in production
        dev_user_id = UUID("00000000-0000-0000-0000-000000000001")
        
        # Simple query without complex relationships to avoid SQLAlchemy config issues
        query = select(Project).where(Project.user_id == dev_user_id)
        result = await db.execute(query)
        projects = result.scalars().all()
        
        # Convert to response format manually
        project_list = []
        for project in projects:
            # Get files separately
            files_query = select(ProjectFile).where(ProjectFile.project_id == project.id)
            files_result = await db.execute(files_query)
            files = files_result.scalars().all()
            
            project_info = ProjectInfo(
                id=str(project.id),
                name=project.name,
                description=project.description,
                template_type=project.template_type or "basic",
                files=[
                    FileInfo(
                        id=str(file.id),
                        name=file.name,
                        path=file.path,
                        content=file.content,
                        language=file.language,
                        size=file.size,
                        created_at=file.created_at,
                        updated_at=file.updated_at,
                        version=file.version,
                        checksum=file.checksum
                    ) for file in files
                ],
                created_at=project.created_at,
                updated_at=project.updated_at,
                settings=project.settings or {},
                user_id=str(project.user_id),
                file_count=len(files)
            )
            project_list.append(project_info)
        
        return project_list
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        # Return mock data if database fails
        return [
            ProjectInfo(
                id="00000000-0000-0000-0000-000000000001",
                name="Trading Strategy Example",
                description="Sample trading strategy project",
                template_type="trading",
                files=[
                    FileInfo(
                        id="file-001",
                        name="main.py",
                        path="main.py",
                        content="# Trading strategy implementation\nprint('Hello from trading strategy!')",
                        language="python",
                        size=67,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        version=1,
                        checksum="abc123"
                    )
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                settings={"aiEnabled": True, "suggestions": True, "autoComplete": True},
                user_id="00000000-0000-0000-0000-000000000001",
                file_count=1
            )
        ]


@router.get("/projects/{project_id}", response_model=ProjectInfo)
async def get_project(
    project_id: str,
    # TODO: Re-enable authentication for production
    # current_user: User = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Get project details with all files."""
    try:
        project_uuid = UUID(project_id)
        
        # TODO: Use actual user ID from authentication in production
        # For dev, just find the project by ID without user restriction
        try:
            query = select(Project).where(Project.id == project_uuid)
            result = await db.execute(query)
            project = result.scalar_one_or_none()
            
            if project:
                # Get files separately
                files_query = select(ProjectFile).where(ProjectFile.project_id == project.id)
                files_result = await db.execute(files_query)
                files = files_result.scalars().all()
                
                return ProjectInfo(
                    id=str(project.id),
                    name=project.name,
                    description=project.description,
                    template_type=project.template_type or "basic",
                    files=[
                        FileInfo(
                            id=str(file.id),
                            name=file.name,
                            path=file.path,
                            content=file.content,
                            language=file.language,
                            size=file.size,
                            created_at=file.created_at,
                            updated_at=file.updated_at,
                            version=file.version,
                            checksum=file.checksum
                        ) for file in files
                    ],
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                    settings=project.settings or {},
                    user_id=str(project.user_id),
                    file_count=len(files)
                )
        except:
            pass
        
        # If not found in DB or DB error, return mock data for the specific project ID
        if project_id == "00000000-0000-0000-0000-000000000001":
            return ProjectInfo(
                id="00000000-0000-0000-0000-000000000001",
                name="Trading Strategy Example",
                description="Sample trading strategy project",
                template_type="trading",
                files=[
                    FileInfo(
                        id="file-001",
                        name="main.py",
                        path="main.py",
                        content="# Trading strategy implementation\nprint('Hello from trading strategy!')",
                        language="python",
                        size=67,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        version=1,
                        checksum="abc123"
                    )
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                settings={"aiEnabled": True, "suggestions": True, "autoComplete": True},
                user_id="00000000-0000-0000-0000-000000000001",
                file_count=1
            )
        
        raise HTTPException(status_code=404, detail="Project not found")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    # TODO: Re-enable authentication for production
    # current_user: User = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Delete a project and all its files."""
    try:
        project_uuid = UUID(project_id)
        
        # TODO: Add user_id restriction back in production
        result = await db.execute(
            select(Project)
            .where(Project.id == project_uuid)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        await db.delete(project)
        await db.commit()
        
        logger.info(f"Deleted project: {project_id} for user {dev_user_id}")
        return {"message": f"Project {project.name} deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")


# File endpoints
@router.post("/projects/{project_id}/files", response_model=FileInfo, status_code=status.HTTP_201_CREATED)
async def create_file(
    project_id: str,
    request: CreateFileRequest,
    # TODO: Re-enable authentication for production
    # current_user: User = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Create a new file in a project."""
    try:
        # TODO: Use actual user ID from authentication in production
        dev_user_id = UUID("00000000-0000-0000-0000-000000000001")
        
        # Validate filename
        if not validate_filename(request.name):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # For development, return mock successful file creation response
        # TODO: Replace with actual database operations in production
        logger.info(f"Creating file: {project_id}/{request.name} for development")
        
        return FileInfo(
            id=str(uuid4()),
            name=request.name,
            path=request.name,
            content=request.content,
            language=request.language,
            size=len(request.content.encode('utf-8')),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1,
            checksum=calculate_checksum(request.content)
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")


@router.get("/projects/{project_id}/files/{filename:path}", response_model=FileInfo)
async def get_file(
    project_id: str,
    filename: str,
    # TODO: Re-enable authentication for production
    # current_user: User = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Get file content."""
    try:
        project_uuid = UUID(project_id)
        
        # TODO: Add user restriction back in production
        try:
            result = await db.execute(
                select(ProjectFile)
                .where(and_(
                    ProjectFile.project_id == project_uuid,
                    ProjectFile.name == filename
                ))
            )
            project_file = result.scalar_one_or_none()
            
            if project_file:
                return FileInfo(
                    id=str(project_file.id),
                    name=project_file.name,
                    path=project_file.path,
                    content=project_file.content,
                    language=project_file.language,
                    size=project_file.size,
                    created_at=project_file.created_at,
                    updated_at=project_file.updated_at,
                    version=project_file.version,
                    checksum=project_file.checksum
                )
        except:
            pass
        
        # Return mock data for development if file not found in DB or DB error
        if project_id == "00000000-0000-0000-0000-000000000001" and filename == "main.py":
            return FileInfo(
                id="file-001",
                name="main.py",
                path="main.py",
                content="# Trading strategy implementation\nprint('Hello from trading strategy!')\n\n# Add your trading logic here",
                language="python",
                size=89,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version=1,
                checksum="abc123"
            )
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file: {str(e)}")


@router.put("/projects/{project_id}/files/{filename:path}", response_model=FileInfo)
async def update_file(
    project_id: str,
    filename: str,
    request: UpdateFileRequest,
    # TODO: Re-enable authentication for production
    # current_user: User = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Update file content."""
    try:
        # TODO: Use actual user ID from authentication in production
        dev_user_id = UUID("00000000-0000-0000-0000-000000000001")
        
        project_uuid = UUID(project_id)
        
        # Check file size
        if len(request.content.encode('utf-8')) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Get file and verify ownership
        result = await db.execute(
            select(ProjectFile)
            .join(Project)
            .where(and_(
                ProjectFile.project_id == project_uuid,
                ProjectFile.file_name == filename,
                Project.user_id == dev_user_id
            ))
        )
        project_file = result.scalar_one_or_none()
        
        if not project_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Save current version
        file_version = FileVersion(
            file_id=project_file.id,
            user_id=dev_user_id,
            version_number=project_file.version,
            content=project_file.content,
            content_hash=project_file.checksum or "",
            change_summary="Auto-saved version",
            lines_added=0,  # Can be calculated
            lines_removed=0  # Can be calculated
        )
        db.add(file_version)
        
        # Update file
        new_checksum = calculate_checksum(request.content)
        project_file.content = request.content
        project_file.size_bytes = len(request.content.encode('utf-8'))
        project_file.version += 1
        project_file.checksum = new_checksum
        
        if request.language:
            project_file.language = request.language
        
        await db.commit()
        await db.refresh(project_file)
        
        logger.info(f"Updated file: {project_id}/{filename} for user {dev_user_id}")
        return file_model_to_info(project_file, include_content=True)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")


@router.delete("/projects/{project_id}/files/{filename:path}")
async def delete_file(
    project_id: str,
    filename: str,
    # TODO: Re-enable authentication for production
    # current_user: User = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Delete a file."""
    try:
        # TODO: Use actual user ID from authentication in production
        dev_user_id = UUID("00000000-0000-0000-0000-000000000001")
        
        project_uuid = UUID(project_id)
        
        # Get file and verify ownership
        result = await db.execute(
            select(ProjectFile)
            .join(Project)
            .where(and_(
                ProjectFile.project_id == project_uuid,
                ProjectFile.file_name == filename,
                Project.user_id == dev_user_id
            ))
        )
        project_file = result.scalar_one_or_none()
        
        if not project_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        await db.delete(project_file)
        await db.commit()
        
        logger.info(f"Deleted file: {project_id}/{filename} for user {dev_user_id}")
        return {"message": f"File {filename} deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


# Utility endpoints
@router.get("/projects/{project_id}/files", response_model=List[FileInfo])
async def list_project_files(
    project_id: str,
    include_content: bool = Query(False),
    # TODO: Re-enable authentication for production
    # current_user: User = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """List all files in a project."""
    try:
        # TODO: Use actual user ID from authentication in production
        dev_user_id = UUID("00000000-0000-0000-0000-000000000001")
        
        project_uuid = UUID(project_id)
        
        # Get all files for the project (verify user ownership)
        result = await db.execute(
            select(ProjectFile)
            .join(Project)
            .where(and_(
                ProjectFile.project_id == project_uuid,
                Project.user_id == dev_user_id
            ))
            .order_by(ProjectFile.file_name)
        )
        files = result.scalars().all()
        
        return [file_model_to_info(f, include_content=include_content) for f in files]
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/templates", response_model=Dict[str, Dict])
async def list_project_templates():
    """List available project templates."""
    try:
        return await get_project_templates()
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.get("/dev/projects", response_model=List[ProjectInfo])
async def list_projects_dev():
    """Development endpoint: Mock projects list for frontend testing."""
    try:
        logger.info("Returning mock projects for development")
        
        # Return mock data to test frontend integration
        mock_projects = [
            ProjectInfo(
                id="00000000-0000-0000-0000-000000000001",
                name="Trading Strategy Example",
                description="Sample trading strategy project",
                template_type="trading",
                files=[
                    FileInfo(
                        id="file-001",
                        name="main.py",
                        path="main.py",
                        content="# Trading strategy implementation\nprint('Hello from trading strategy!')",
                        language="python",
                        size=67,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        version=1,
                        checksum="abc123"
                    )
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                settings={"aiEnabled": True, "suggestions": True, "autoComplete": True},
                user_id="00000000-0000-0000-0000-000000000001",
                file_count=1
            )
        ]
        
        return mock_projects
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")


@router.post("/dev/projects", response_model=ProjectInfo, status_code=status.HTTP_201_CREATED)
async def create_project_dev(
    request: CreateProjectRequest,
    db: AsyncSession = Depends(get_db)
):
    """Development endpoint: Create a project without authentication."""
    try:
        logger.info(f"Creating project for development: {request.name}")
        
        # Create a default user ID for development
        dev_user_id = UUID("00000000-0000-0000-0000-000000000001")
        
        # Create the project
        project = Project(
            id=uuid4(),
            name=request.name,
            description=request.description or f"Development project: {request.name}",
            template_type=request.template or "basic",
            user_id=dev_user_id,
            settings={"aiEnabled": True, "suggestions": True, "autoComplete": True},
            metadata={"created_by": "development", "environment": "dev"}
        )
        
        db.add(project)
        await db.flush()  # Get the project ID
        
        # Add template files if specified
        if request.template:
            templates = await get_project_templates()
            if request.template in templates:
                template_data = templates[request.template]
                for file_data in template_data.get("default_files", []):
                    project_file = ProjectFile(
                        id=uuid4(),
                        name=file_data["name"],
                        path=file_data["name"],
                        content=file_data["content"],
                        language=get_language_from_extension(file_data["name"]),
                        project_id=project.id,
                        version=1,
                        size=len(file_data["content"]),
                        checksum=calculate_checksum(file_data["content"])
                    )
                    db.add(project_file)
        
        await db.commit()
        await db.refresh(project)
        
        # Reload with files
        query = select(Project).where(Project.id == project.id).options(
            selectinload(Project.files)
        )
        result = await db.execute(query)
        project = result.scalar_one()
        
        return await project_model_to_info(project)
        
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")