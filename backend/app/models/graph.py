from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str

class GraphExpandResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    has_more: bool = False
    total_connected: int = 0

class NodeDetailResponse(BaseModel):
    node: GraphNode
    metadata: Optional[Dict[str, Any]] = None
