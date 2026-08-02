from opensearchpy import OpenSearch
from backend.app.config import settings
from backend.app.models.document import DocumentMetadata, SearchResponse, DocumentSearchResult

class OpenSearchClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenSearchClient, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self.client = OpenSearch(
            hosts=[{'host': settings.OPENSEARCH_HOST, 'port': settings.OPENSEARCH_PORT}],
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        self.index_name = settings.INDEX_NAME

    def initialize(self):
        if not self.client.indices.exists(index=self.index_name):
            mappings = {
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "kuromoji_analyzer": {
                                "type": "custom",
                                "tokenizer": "kuromoji_tokenizer",
                                "filter": ["kuromoji_baseform", "kuromoji_part_of_speech", "cjk_width", "lowercase"]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "doc_id": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "kuromoji_analyzer"},
                        "ocr_text": {"type": "text", "analyzer": "kuromoji_analyzer"},
                        "keywords": {"type": "keyword"},
                        "equipment_nos": {"type": "keyword"},
                        "related_doc_ids": {"type": "keyword"},
                        "pdf_path": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "author": {"type": "keyword"},
                        "created_date": {"type": "keyword"},
                        "updated_date": {"type": "keyword"},
                        "department": {"type": "keyword"},
                        "document_type": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "version": {"type": "keyword"},
                        "classification": {"type": "keyword"},
                        "facility": {"type": "keyword"},
                        "building": {"type": "keyword"},
                        "floor": {"type": "keyword"},
                        "room": {"type": "keyword"},
                        "system_name": {"type": "keyword"},
                        "subsystem": {"type": "keyword"},
                        "manufacturer": {"type": "keyword"},
                        "model_number": {"type": "keyword"},
                        "serial_number": {"type": "keyword"},
                        "installation_date": {"type": "keyword"},
                        "inspection_date": {"type": "keyword"},
                        "next_inspection_date": {"type": "keyword"},
                        "remarks": {"type": "text", "analyzer": "kuromoji_analyzer"},
                        "tags": {"type": "keyword"},
                    }
                }
            }
            self.client.indices.create(index=self.index_name, body=mappings)

    def index_document(self, doc: DocumentMetadata):
        self.client.index(
            index=self.index_name,
            id=doc.doc_id,
            body=doc.model_dump()
        )

    def bulk_index(self, docs: list[DocumentMetadata]):
        from opensearchpy.helpers import bulk
        actions = [
            {
                "_index": self.index_name,
                "_id": doc.doc_id,
                "_source": doc.model_dump()
            }
            for doc in docs
        ]
        bulk(self.client, actions)

    def search(self, query: str, filters: dict | None, page: int, size: int) -> SearchResponse:
        body = {
            "from": (page - 1) * size,
            "size": size,
            "query": {
                "bool": {
                    "must": []
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "ocr_text": {},
                    "remarks": {}
                }
            }
        }

        if query:
            body["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": ["title", "ocr_text", "remarks", "keywords", "equipment_nos"]
                }
            })
        else:
            body["query"]["bool"]["must"].append({"match_all": {}})

        if filters:
            for k, v in filters.items():
                body["query"]["bool"]["filter"] = body["query"]["bool"].get("filter", [])
                body["query"]["bool"]["filter"].append({"term": {k: v}})

        res = self.client.search(index=self.index_name, body=body)
        
        results = []
        for hit in res['hits']['hits']:
            source = hit['_source']
            highlights = hit.get('highlight', {})
            snippet = highlights.get('ocr_text', [""])[0] if highlights.get('ocr_text') else source.get('ocr_text', '')[:200]
            
            results.append(DocumentSearchResult(
                doc_id=source.get('doc_id', hit['_id']),
                title=source.get('title', ''),
                score=hit['_score'],
                snippet=snippet,
                highlights=highlights
            ))

        return SearchResponse(
            results=results,
            total=res['hits']['total']['value'],
            page=page,
            size=size
        )

    def get_document(self, doc_id: str) -> DocumentMetadata | None:
        try:
            res = self.client.get(index=self.index_name, id=doc_id)
            return DocumentMetadata(**res['_source'])
        except Exception:
            return None

    def close(self):
        self.client.close()

opensearch_client = OpenSearchClient()
