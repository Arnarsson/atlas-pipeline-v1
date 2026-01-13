"""
Document Processing API Routes

Endpoints for uploading and extracting content from documents.
Supports PDF, DOCX, XLSX, and images with automatic engine selection.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.processors import DocumentExtractor, ExtractionResult, get_document_extractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


class ExtractionResponse(BaseModel):
    """API response for document extraction."""
    success: bool
    filename: str
    file_hash: str
    document_type: str
    file_size_bytes: int
    page_count: int
    engine_used: str
    extraction_time_ms: float
    full_text: str
    element_count: int
    table_count: int
    confidence_score: float
    is_scanned: bool
    ocr_applied: bool
    warnings: List[str]
    errors: List[str]


class BatchExtractionResponse(BaseModel):
    """Response for batch extraction."""
    total_files: int
    successful: int
    failed: int
    results: List[ExtractionResponse]


@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    force_engine: Optional[str] = Query(
        None,
        description="Force specific engine: unstructured, azure_document_intelligence, fallback_text"
    ),
):
    """
    Extract text and structure from a document.

    Supported formats:
    - PDF (native and scanned)
    - DOCX/DOC
    - XLSX/XLS
    - Images (PNG, JPG, TIFF)
    - TXT, CSV

    Engine selection:
    - unstructured (default for native documents)
    - azure_document_intelligence (for scanned/large files)
    - fallback_text (when primary engines fail)
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    # Read content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    # Check file size (max 50MB)
    max_size = 50 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {max_size // 1024 // 1024}MB"
        )

    # Parse force_engine
    engine = None
    if force_engine:
        from app.processors.document_extractor import ExtractionEngine
        try:
            engine = ExtractionEngine(force_engine)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid engine. Must be one of: unstructured, azure_document_intelligence, fallback_text"
            )

    # Extract
    try:
        extractor = get_document_extractor()
        result = await extractor.extract(
            file_content=content,
            filename=file.filename,
            force_engine=engine,
        )

        return ExtractionResponse(
            success=True,
            filename=result.filename,
            file_hash=result.file_hash,
            document_type=result.document_type.value,
            file_size_bytes=result.file_size_bytes,
            page_count=result.page_count,
            engine_used=result.engine_used.value,
            extraction_time_ms=result.extraction_time_ms,
            full_text=result.full_text,
            element_count=len(result.elements),
            table_count=len(result.tables),
            confidence_score=result.confidence_score,
            is_scanned=result.is_scanned,
            ocr_applied=result.ocr_applied,
            warnings=result.warnings,
            errors=result.errors,
        )

    except Exception as e:
        logger.error(f"Extraction failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/extract/batch", response_model=BatchExtractionResponse)
async def extract_documents_batch(
    files: List[UploadFile] = File(...),
):
    """
    Extract text from multiple documents.

    Maximum 10 files per batch.
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files per batch"
        )

    extractor = get_document_extractor()
    results = []
    successful = 0
    failed = 0

    for file in files:
        try:
            content = await file.read()
            if not content:
                results.append(ExtractionResponse(
                    success=False,
                    filename=file.filename or "unknown",
                    file_hash="",
                    document_type="unknown",
                    file_size_bytes=0,
                    page_count=0,
                    engine_used="none",
                    extraction_time_ms=0,
                    full_text="",
                    element_count=0,
                    table_count=0,
                    confidence_score=0,
                    is_scanned=False,
                    ocr_applied=False,
                    warnings=[],
                    errors=["Empty file"],
                ))
                failed += 1
                continue

            result = await extractor.extract(
                file_content=content,
                filename=file.filename,
            )

            results.append(ExtractionResponse(
                success=True,
                filename=result.filename,
                file_hash=result.file_hash,
                document_type=result.document_type.value,
                file_size_bytes=result.file_size_bytes,
                page_count=result.page_count,
                engine_used=result.engine_used.value,
                extraction_time_ms=result.extraction_time_ms,
                full_text=result.full_text,
                element_count=len(result.elements),
                table_count=len(result.tables),
                confidence_score=result.confidence_score,
                is_scanned=result.is_scanned,
                ocr_applied=result.ocr_applied,
                warnings=result.warnings,
                errors=result.errors,
            ))
            successful += 1

        except Exception as e:
            logger.error(f"Batch extraction failed for {file.filename}: {e}")
            results.append(ExtractionResponse(
                success=False,
                filename=file.filename or "unknown",
                file_hash="",
                document_type="unknown",
                file_size_bytes=0,
                page_count=0,
                engine_used="none",
                extraction_time_ms=0,
                full_text="",
                element_count=0,
                table_count=0,
                confidence_score=0,
                is_scanned=False,
                ocr_applied=False,
                warnings=[],
                errors=[str(e)],
            ))
            failed += 1

    return BatchExtractionResponse(
        total_files=len(files),
        successful=successful,
        failed=failed,
        results=results,
    )


@router.get("/extract/status")
async def get_extractor_status():
    """
    Get document extractor status and capabilities.
    """
    extractor = get_document_extractor()

    return {
        "status": "operational",
        "engines": {
            "unstructured": {
                "available": extractor._unstructured_available,
                "primary": True,
                "description": "Open source document extraction"
            },
            "azure_document_intelligence": {
                "available": extractor._azure_available,
                "primary": False,
                "description": "Azure OCR for scanned documents"
            },
            "fallback_text": {
                "available": True,
                "primary": False,
                "description": "Basic text extraction fallback"
            }
        },
        "supported_formats": [
            "PDF (native and scanned)",
            "DOCX/DOC",
            "XLSX/XLS",
            "PPTX",
            "TXT",
            "CSV",
            "PNG/JPG/TIFF/BMP (images)"
        ],
        "max_file_size_mb": 50,
        "max_batch_size": 10,
        "feature_flags": {
            "USE_AZURE_OCR": extractor.use_azure_fallback,
        }
    }
