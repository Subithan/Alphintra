from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.services.feature_engineer import FeatureEngineer
from app.services.storage_manager import StorageManager
from app.models.dataset import Dataset

router = APIRouter()

class FeatureEngineeringRequest(BaseModel):
    workflow_definition: Dict[str, Any] = Field(..., description="The workflow definition as a JSON object.")
    dataset_id: str = Field(..., description="The ID of the dataset to use for feature engineering.")
    n_features_to_select: int = Field(20, gt=0, le=100, description="The number of top features to select.")

class FeatureEngineeringResponse(BaseModel):
    selected_features: List[str]
    generated_features_count: int
    dataset_id: str

async def get_dataset_by_id(dataset_id: str, user_id: str, db: AsyncSession) -> Dataset:
    """
    Retrieves a dataset by its ID, ensuring the user has access.
    """
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == UUID(dataset_id),
            or_(
                Dataset.user_id == UUID(user_id),
                Dataset.is_public == True
            )
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset with id {dataset_id} not found or not accessible.")
    return dataset

@router.post("/", response_model=FeatureEngineeringResponse)
async def run_feature_engineering(
    request: FeatureEngineeringRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Runs the feature engineering pipeline on a given workflow and dataset.
    Generates a set of new features and then selects the most promising ones
    based on mutual information.
    """
    dataset = await get_dataset_by_id(request.dataset_id, str(user_id), db)

    storage_manager = StorageManager()
    data = await storage_manager.retrieve_dataset(dataset)

    if data is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve dataset data from storage.")

    # Initialize the feature engineer with the workflow and data
    feature_engineer = FeatureEngineer(request.workflow_definition, data)

    # Generate a rich set of features
    generated_features_df = feature_engineer.generate_features()

    # Select the best features from the generated set
    selected_features_df = feature_engineer.select_features(
        n_features_to_select=request.n_features_to_select
    )

    return {
        "selected_features": selected_features_df.columns.tolist(),
        "generated_features_count": len(generated_features_df.columns),
        "dataset_id": request.dataset_id,
    }
