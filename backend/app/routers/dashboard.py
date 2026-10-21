from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError
from app.services.dashboard_service import DashboardService
from app.models.progress import DashboardSummaryResponse, LevelChangeRequest

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardSummaryResponse)
async def get_dashboard():
    """Retrieve full dashboard summary for the active learner."""
    try:
        return await DashboardService.get_dashboard_summary()
    except (PyMongoError, RuntimeError) as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Could not load the dashboard; please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load the dashboard. Please try again."
        )

@router.post("/level")
async def update_learner_level(request: LevelChangeRequest):
    """Change the learner's active CEFR level (A1, A2, B1, B2, C1, C2)."""
    try:
        result = await DashboardService.update_learner_level(request.cefr_level.upper())
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except (PyMongoError, RuntimeError) as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Your level change was not confirmed; please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update your CEFR level. Please try again."
        )

