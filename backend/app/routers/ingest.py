from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.models.document import DocumentIngestRequest, DocumentMetadata
from backend.app.services.ingest_service import ingest_service
import json

router = APIRouter(prefix="/api/ingest", tags=["ingest"])

@router.post("/documents")
async def ingest_documents(request: DocumentIngestRequest):
    try:
        return ingest_service.ingest_documents(request.documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_documents(file: UploadFile = File(...)):
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON file upload is supported currently")
    
    try:
        content = await file.read()
        data = json.loads(content)
        if isinstance(data, list):
            docs = [DocumentMetadata(**item) for item in data]
        else:
            docs = [DocumentMetadata(**data)]
            
        return ingest_service.ingest_documents(docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
