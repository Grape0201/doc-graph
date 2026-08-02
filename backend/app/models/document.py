from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class DocumentMetadata(BaseModel):
    doc_id: str
    title: str
    related_doc_ids: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    equipment_nos: List[str] = Field(default_factory=list)
    pdf_path: str = ""
    ocr_text: str = ""
    category: str = ""
    author: str = ""
    created_date: str = ""
    updated_date: str = ""
    department: str = ""
    document_type: str = ""
    status: str = ""
    version: str = ""
    classification: str = ""
    facility: str = ""
    building: str = ""
    floor: str = ""
    room: str = ""
    system_name: str = ""
    subsystem: str = ""
    manufacturer: str = ""
    model_number: str = ""
    serial_number: str = ""
    installation_date: str = ""
    inspection_date: str = ""
    next_inspection_date: str = ""
    remarks: str = ""
    tags: List[str] = Field(default_factory=list)

class DocumentIngestRequest(BaseModel):
    documents: List[DocumentMetadata]

class DocumentSearchResult(BaseModel):
    doc_id: str
    title: str
    score: float
    snippet: str = ""
    highlights: Dict[str, List[str]] = Field(default_factory=dict)

class SearchResponse(BaseModel):
    results: List[DocumentSearchResult]
    total: int
    page: int
    size: int
