from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import RegulatoryResultObject
from backend.models import KBDocument
from backend.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Regulatory Clarity (RAG)"])

@router.get("/search", response_model=RegulatoryResultObject)
def search_regulatory_knowledge(
    q: str = Query(..., description="Query regarding RBI KYC, AML, PMLA, DICGC, or Ombudsman regulations"),
    db: Session = Depends(get_db)
):
    return KnowledgeService.query_regulatory_corpus(db=db, query_text=q)

@router.get("/documents")
def list_regulatory_documents(db: Session = Depends(get_db)):
    KnowledgeService.seed_corpus_if_empty(db)
    docs = db.query(KBDocument).all()
    results = []
    for d in docs:
        results.append({
            "id": d.id,
            "title": d.title,
            "document_type": d.document_type,
            "version": d.version,
            "effective_date": d.effective_date,
            "source_url": d.source_url,
            "section_count": len(d.chunks),
            "sections": [
                {
                    "section_number": c.section_number,
                    "section_title": c.section_title,
                    "content": c.content
                }
                for c in d.chunks
            ]
        })
    return results
