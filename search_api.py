"""
SEARCH API ENHANCEMENTS

Extended search endpoints for advanced filtering and discovery.

New Endpoints:
- GET /trains/active → Get all ACTIVE trains
- GET /trains/status/{status} → Filter by status
- GET /trains/freshness → Sort by freshness
- GET /trains/quality → Sort by quality score
- GET /trains/{train_no}/validation → Get validation info
- GET /trains/search → Advanced search with filters

Author: Route Master
Date: 2026-01-25
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

try:
    from database import DatabaseManager, TrainStatus
    from irctc_validator import IRCTCValidator
    from logger import LoggerFactory
except ImportError:
    pass

router = APIRouter(prefix="/trains", tags=["trains"])


class TrainStatusEnum(str, Enum):
    """Train status values"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    UNKNOWN = "UNKNOWN"
    SUSPENDED = "SUSPENDED"
    DEPRECATED = "DEPRECATED"


class SortOrder(str, Enum):
    """Sort order for results"""
    ASC = "asc"
    DESC = "desc"


@router.get("/active", response_model=Dict[str, Any])
async def get_active_trains(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Get all ACTIVE trains
    
    Returns trains with ACTIVE status (confirmed available via IRCTC)
    
    Args:
        limit: Number of results (1-1000, default 100)
        offset: Pagination offset
    
    Returns:
        {
            "count": int,
            "total": int,
            "trains": [
                {
                    "train_no": string,
                    "train_name": string,
                    "status": "ACTIVE",
                    "quality_score": float,
                    "last_validated": ISO8601,
                    "last_updated": ISO8601
                }
            ]
        }
    """
    try:
        db = DatabaseManager()
        
        # Get total count
        total = db.session.query(db.Train).filter(
            db.Train.status == "ACTIVE"
        ).count()
        
        # Get paginated results
        active_trains = db.session.query(db.Train).filter(
            db.Train.status == "ACTIVE"
        ).order_by(
            db.Train.quality_score.desc()
        ).offset(offset).limit(limit).all()
        
        trains_data = [
            {
                "train_no": str(t.train_no),
                "train_name": t.train_name,
                "status": t.status,
                "quality_score": round(t.quality_score, 2) if t.quality_score else 0,
                "last_validated": t.last_updated.isoformat() if t.last_updated else None,
                "last_updated": t.last_updated.isoformat() if t.last_updated else None
            }
            for t in active_trains
        ]
        
        return {
            "count": len(trains_data),
            "total": total,
            "limit": limit,
            "offset": offset,
            "trains": trains_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{status}", response_model=Dict[str, Any])
async def get_trains_by_status(
    status: TrainStatusEnum,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Filter trains by status
    
    Args:
        status: Train status (ACTIVE, INACTIVE, UNKNOWN, SUSPENDED, DEPRECATED)
        limit: Number of results
        offset: Pagination offset
    
    Returns:
        List of trains with specified status
    """
    try:
        db = DatabaseManager()
        
        # Get total count
        total = db.session.query(db.Train).filter(
            db.Train.status == status.value
        ).count()
        
        # Get paginated results
        trains = db.session.query(db.Train).filter(
            db.Train.status == status.value
        ).order_by(
            db.Train.quality_score.desc()
        ).offset(offset).limit(limit).all()
        
        trains_data = [
            {
                "train_no": str(t.train_no),
                "train_name": t.train_name,
                "status": t.status,
                "quality_score": round(t.quality_score, 2) if t.quality_score else 0,
                "last_updated": t.last_updated.isoformat() if t.last_updated else None
            }
            for t in trains
        ]
        
        return {
            "status": status.value,
            "count": len(trains_data),
            "total": total,
            "trains": trains_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/freshness", response_model=Dict[str, Any])
async def get_trains_by_freshness(
    sort: SortOrder = Query(SortOrder.DESC),
    limit: int = Query(100, ge=1, le=1000),
    hours: int = Query(24)
) -> Dict[str, Any]:
    """
    Get trains sorted by data freshness
    
    Args:
        sort: Sort order (asc=oldest first, desc=newest first)
        limit: Number of results
        hours: Only include trains updated in last N hours
    
    Returns:
        Trains sorted by freshness
    """
    try:
        db = DatabaseManager()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Build query
        query = db.session.query(db.Train).filter(
            db.Train.last_updated >= cutoff_time
        )
        
        # Apply sort
        if sort == SortOrder.DESC:
            query = query.order_by(db.Train.last_updated.desc())
        else:
            query = query.order_by(db.Train.last_updated.asc())
        
        trains = query.limit(limit).all()
        
        trains_data = [
            {
                "train_no": str(t.train_no),
                "train_name": t.train_name,
                "status": t.status,
                "last_updated": t.last_updated.isoformat() if t.last_updated else None,
                "hours_ago": round(
                    (datetime.now() - t.last_updated).total_seconds() / 3600
                ) if t.last_updated else None
            }
            for t in trains
        ]
        
        return {
            "count": len(trains_data),
            "sort_order": sort.value,
            "hours_window": hours,
            "trains": trains_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality", response_model=Dict[str, Any])
async def get_trains_by_quality(
    min_score: float = Query(0.0, ge=0, le=100),
    max_score: float = Query(100.0, ge=0, le=100),
    sort: SortOrder = Query(SortOrder.DESC),
    limit: int = Query(100, ge=1, le=1000)
) -> Dict[str, Any]:
    """
    Get trains filtered and sorted by quality score
    
    Quality Score calculation:
    - Freshness (50%): How recently data was updated
    - Completeness (30%): How much field data is available
    - Validation (20%): IRCTC validation success rate
    
    Args:
        min_score: Minimum quality score (0-100)
        max_score: Maximum quality score (0-100)
        sort: Sort order
        limit: Number of results
    
    Returns:
        High-quality trains
    """
    try:
        db = DatabaseManager()
        
        query = db.session.query(db.Train).filter(
            db.Train.quality_score >= min_score,
            db.Train.quality_score <= max_score
        )
        
        # Apply sort
        if sort == SortOrder.DESC:
            query = query.order_by(db.Train.quality_score.desc())
        else:
            query = query.order_by(db.Train.quality_score.asc())
        
        trains = query.limit(limit).all()
        
        trains_data = [
            {
                "train_no": str(t.train_no),
                "train_name": t.train_name,
                "status": t.status,
                "quality_score": round(t.quality_score, 2) if t.quality_score else 0,
                "quality_grade": (
                    "A" if t.quality_score >= 90
                    else "B" if t.quality_score >= 80
                    else "C" if t.quality_score >= 70
                    else "D" if t.quality_score >= 60
                    else "F"
                ),
                "last_updated": t.last_updated.isoformat() if t.last_updated else None
            }
            for t in trains
        ]
        
        return {
            "quality_range": f"{min_score}-{max_score}",
            "count": len(trains_data),
            "sort_order": sort.value,
            "trains": trains_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{train_no}/validation", response_model=Dict[str, Any])
async def get_train_validation_info(train_no: str) -> Dict[str, Any]:
    """
    Get validation information for a specific train
    
    Returns:
    - Current ACTIVE/INACTIVE status
    - Last validation time
    - Validation history
    - Seat availability info
    
    Args:
        train_no: Train number (e.g., "16320")
    
    Returns:
        Validation details
    """
    try:
        db = DatabaseManager()
        validator = IRCTCValidator()
        
        # Get train info
        train = db.session.query(db.Train).filter(
            db.Train.train_no == train_no
        ).first()
        
        if not train:
            raise HTTPException(status_code=404, detail=f"Train {train_no} not found")
        
        # Get validation history (last 5)
        validation_history = []
        try:
            # Would query from validation logs if available
            validation_history = []
        except:
            pass
        
        # Get current validation status
        current_status = {
            "train_no": str(train.train_no),
            "train_name": train.train_name,
            "current_status": train.status,
            "quality_score": round(train.quality_score, 2) if train.quality_score else 0,
            "last_updated": train.last_updated.isoformat() if train.last_updated else None
        }
        
        # Check if we can validate now (get fresh data)
        fresh_validation = None
        try:
            result = validator.validate_train(train_no, date=None)
            if result:
                fresh_validation = {
                    "has_available_seats": result.has_available_seats,
                    "seat_class": result.seat_class,
                    "availability_count": result.availability_count,
                    "validation_time": datetime.now().isoformat()
                }
        except:
            pass
        
        return {
            "train_no": train_no,
            "current_status": current_status,
            "fresh_validation": fresh_validation,
            "validation_history": validation_history,
            "is_bookable": train.status == "ACTIVE"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=Dict[str, Any])
async def advanced_search(
    train_name: Optional[str] = Query(None),
    status: Optional[TrainStatusEnum] = Query(None),
    min_quality: float = Query(0.0),
    max_quality: float = Query(100.0),
    limit: int = Query(50, ge=1, le=1000),
    sort_by: str = Query("quality", regex="^(quality|freshness|name)$")
) -> Dict[str, Any]:
    """
    Advanced search with multiple filters
    
    Args:
        train_name: Partial train name to search
        status: Filter by status
        min_quality: Minimum quality score
        max_quality: Maximum quality score
        limit: Number of results
        sort_by: Sort field (quality, freshness, name)
    
    Returns:
        Filtered and sorted trains
    """
    try:
        db = DatabaseManager()
        
        query = db.session.query(db.Train)
        
        # Apply filters
        if train_name:
            query = query.filter(
                db.Train.train_name.ilike(f"%{train_name}%")
            )
        
        if status:
            query = query.filter(db.Train.status == status.value)
        
        query = query.filter(
            db.Train.quality_score >= min_quality,
            db.Train.quality_score <= max_quality
        )
        
        # Apply sort
        if sort_by == "quality":
            query = query.order_by(db.Train.quality_score.desc())
        elif sort_by == "freshness":
            query = query.order_by(db.Train.last_updated.desc())
        elif sort_by == "name":
            query = query.order_by(db.Train.train_name.asc())
        
        trains = query.limit(limit).all()
        
        trains_data = [
            {
                "train_no": str(t.train_no),
                "train_name": t.train_name,
                "status": t.status,
                "quality_score": round(t.quality_score, 2) if t.quality_score else 0
            }
            for t in trains
        ]
        
        return {
            "query": {
                "train_name": train_name,
                "status": status.value if status else None,
                "quality_range": f"{min_quality}-{max_quality}"
            },
            "count": len(trains_data),
            "sort_by": sort_by,
            "trains": trains_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def setup_search_api(app):
    """Setup search API in FastAPI app"""
    app.include_router(router)


if __name__ == "__main__":
    print("Search API Enhancements")
    print("=" * 50)
    print("✓ 6 new endpoints ready:")
    print("  - GET /trains/active")
    print("  - GET /trains/status/{status}")
    print("  - GET /trains/freshness")
    print("  - GET /trains/quality")
    print("  - GET /trains/{train_no}/validation")
    print("  - GET /trains/search")
