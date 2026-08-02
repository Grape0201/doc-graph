from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENSEARCH_HOST: str = "localhost"
    OPENSEARCH_PORT: int = 9200
    NEO4J_URI: str = "bolt://localhost:7687"
    PDF_STORAGE_PATH: str = "/tmp/pdf_storage"
    INDEX_NAME: str = "doc-graph-documents"

    class Config:
        env_file = ".env"

settings = Settings()
