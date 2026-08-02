from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.app.routers import ingest, search, graph
from backend.app.clients.opensearch_client import opensearch_client
from backend.app.clients.neo4j_client import neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Doc-Graph API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(graph.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Neo4j constraints...")
    try:
        neo4j_client.initialize()
    except Exception as e:
        logger.error(f"Error initializing Neo4j: {e}")

    logger.info("Initializing OpenSearch index...")
    try:
        opensearch_client.initialize()
    except Exception as e:
        logger.error(f"Error initializing OpenSearch: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing Neo4j connection...")
    neo4j_client.close()
    
    logger.info("Closing OpenSearch connection...")
    opensearch_client.close()

@app.get("/")
def root():
    return {"message": "Welcome to Doc-Graph API"}
