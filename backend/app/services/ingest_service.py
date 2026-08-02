from backend.app.models.document import DocumentMetadata
from backend.app.clients.opensearch_client import opensearch_client
from backend.app.clients.neo4j_client import neo4j_client

class IngestService:
    def ingest_documents(self, docs: list[DocumentMetadata]) -> dict:
        # 1. Bulk index to OpenSearch
        opensearch_client.bulk_index(docs)

        # 2-5. Ingest into Neo4j
        for doc in docs:
            # Create Document node
            props = {k: v for k, v in doc.model_dump().items() if k not in ["related_doc_ids", "keywords", "equipment_nos", "ocr_text", "tags"]}
            neo4j_client.create_document_node(doc.doc_id, doc.title, props)

        for doc in docs:
            # Create REFERENCES edges
            for related_id in doc.related_doc_ids:
                neo4j_client.create_reference_edge(doc.doc_id, related_id)
            
            # Create Keyword nodes and edges
            for kw in doc.keywords:
                neo4j_client.create_keyword_node_and_edge(doc.doc_id, kw)
                
            # Create Equipment nodes and edges
            for eq in doc.equipment_nos:
                neo4j_client.create_equipment_node_and_edge(doc.doc_id, eq)

        return {
            "status": "success",
            "message": f"Ingested {len(docs)} documents successfully."
        }

ingest_service = IngestService()
