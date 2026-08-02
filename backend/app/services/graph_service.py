from backend.app.clients.neo4j_client import neo4j_client
from backend.app.clients.opensearch_client import opensearch_client
from backend.app.models.graph import GraphExpandResponse, NodeDetailResponse

class GraphService:
    def expand(self, node_id: str, node_type: str, hops: int, limit: int) -> GraphExpandResponse:
        hops = min(hops, 3)
        limit = min(limit, 200)
        return neo4j_client.expand_graph(node_id, node_type, hops, limit)

    def get_node_detail(self, node_id: str, node_type: str) -> NodeDetailResponse | None:
        node = neo4j_client.get_node_detail(node_id, node_type)
        if not node:
            return None

        metadata = None
        if node_type == "Document":
            doc = opensearch_client.get_document(node_id)
            if doc:
                metadata = doc.model_dump()
        else:
            # Keyword / Equipment: 接続されている文書数を取得
            connected_count = neo4j_client.count_connected_documents(node_id, node_type)
            metadata = {
                "connected_document_count": connected_count,
            }

        return NodeDetailResponse(node=node, metadata=metadata)

graph_service = GraphService()
