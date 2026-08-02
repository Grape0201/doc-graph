from fastapi import APIRouter, Query, HTTPException
from backend.app.services.search_service import search_service
from backend.app.models.document import SearchResponse

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(default="", description="Search query"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100)
):
    try:
        return search_service.search(q, None, page, size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
