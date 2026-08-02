from fastapi import APIRouter, Query, HTTPException
from backend.app.services.graph_service import graph_service
from backend.app.models.graph import GraphExpandResponse, NodeDetailResponse

router = APIRouter(prefix="/api/graph", tags=["graph"])

@router.get("/expand", response_model=GraphExpandResponse)
async def expand_graph(
    node_id: str = Query(...),
    node_type: str = Query(default="Document"),
    hops: int = Query(default=1, ge=1, le=3),
    limit: int = Query(default=50, ge=1, le=200)
):
    try:
        return graph_service.expand(node_id, node_type, hops, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/node/{node_type}/{node_id}", response_model=NodeDetailResponse)
async def get_node_detail(node_type: str, node_id: str):
    try:
        res = graph_service.get_node_detail(node_id, node_type)
        if not res:
            raise HTTPException(status_code=404, detail="Node not found")
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
