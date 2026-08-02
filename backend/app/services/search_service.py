from backend.app.clients.opensearch_client import opensearch_client
from backend.app.models.document import SearchResponse

class SearchService:
    def search(self, query: str, filters: dict | None, page: int, size: int) -> SearchResponse:
        return opensearch_client.search(query, filters, page, size)

search_service = SearchService()
