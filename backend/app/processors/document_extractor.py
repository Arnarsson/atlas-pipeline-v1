"""
Document Extractor - Extract text and metadata from PDF, DOCX, XLSX, and images.

Uses `unstructured` as primary extraction engine with Azure Document Intelligence
as fallback for scanned documents or complex layouts.

Feature Flags:
- USE_AZURE_OCR: Enable Azure Document Intelligence fallback
- NOTIFY_IMMEDIATE: Send immediate notifications for critical extractions
"""

import hashlib
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class ExtractionEngine(str, Enum):
    """Document extraction engine used."""
    UNSTRUCTURED = "unstructured"
    AZURE_DOCUMENT_INTELLIGENCE = "azure_document_intelligence"
    FALLBACK_TEXT = "fallback_text"


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    DOC = "doc"
    XLS = "xls"
    PPTX = "pptx"
    TXT = "txt"
    CSV = "csv"
    IMAGE = "image"  # PNG, JPG, JPEG, TIFF, BMP
    UNKNOWN = "unknown"


@dataclass
class ExtractedElement:
    """A single extracted element from a document."""
    element_type: str  # title, narrative_text, table, list_item, image, etc.
    text: str
    page_number: Optional[int] = None
    coordinates: Optional[Dict[str, float]] = None  # bounding box
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableData:
    """Extracted table data."""
    headers: List[str]
    rows: List[List[str]]
    page_number: Optional[int] = None
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    """Complete extraction result from a document."""
    # Document metadata
    filename: str
    file_hash: str  # SHA-256 for audit
    document_type: DocumentType
    file_size_bytes: int
    page_count: int

    # Extraction info
    engine_used: ExtractionEngine
    extraction_time_ms: float
    extracted_at: datetime

    # Content
    full_text: str
    elements: List[ExtractedElement]
    tables: List[TableData]

    # Quality
    confidence_score: float
    is_scanned: bool
    ocr_applied: bool

    # Errors/warnings
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "filename": self.filename,
            "file_hash": self.file_hash,
            "document_type": self.document_type.value,
            "file_size_bytes": self.file_size_bytes,
            "page_count": self.page_count,
            "engine_used": self.engine_used.value,
            "extraction_time_ms": self.extraction_time_ms,
            "extracted_at": self.extracted_at.isoformat(),
            "full_text": self.full_text,
            "elements": [
                {
                    "element_type": e.element_type,
                    "text": e.text,
                    "page_number": e.page_number,
                    "confidence": e.confidence,
                }
                for e in self.elements
            ],
            "tables": [
                {
                    "headers": t.headers,
                    "rows": t.rows,
                    "page_number": t.page_number,
                }
                for t in self.tables
            ],
            "confidence_score": self.confidence_score,
            "is_scanned": self.is_scanned,
            "ocr_applied": self.ocr_applied,
            "warnings": self.warnings,
            "errors": self.errors,
        }


class DocumentExtractor:
    """
    Extract text and structured data from documents.

    Primary: unstructured library
    Fallback: Azure Document Intelligence (for scanned/complex documents)

    Automatic engine selection based on:
    - File type (scanned PDFs → Azure)
    - File size (>5MB → Azure for better performance)
    - Content detection (low text density → Azure OCR)
    """

    # File size threshold for Azure fallback (5MB)
    AZURE_SIZE_THRESHOLD = 5 * 1024 * 1024

    # Minimum text density to consider document as "native" (not scanned)
    MIN_TEXT_DENSITY = 0.1  # 10% of pages should have text

    def __init__(
        self,
        use_azure_fallback: bool = True,
        azure_endpoint: Optional[str] = None,
        azure_key: Optional[str] = None,
    ):
        """
        Initialize document extractor.

        Args:
            use_azure_fallback: Enable Azure Document Intelligence fallback
            azure_endpoint: Azure Form Recognizer endpoint
            azure_key: Azure API key
        """
        self.use_azure_fallback = use_azure_fallback and os.getenv("USE_AZURE_OCR", "false").lower() == "true"
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_DOCUMENT_ENDPOINT")
        self.azure_key = azure_key or os.getenv("AZURE_DOCUMENT_KEY")

        # Check unstructured availability
        self._unstructured_available = self._check_unstructured()

        # Check Azure availability
        self._azure_available = self._check_azure() if self.use_azure_fallback else False

        logger.info(
            f"DocumentExtractor initialized: unstructured={self._unstructured_available}, "
            f"azure={self._azure_available}"
        )

    def _check_unstructured(self) -> bool:
        """Check if unstructured library is available."""
        try:
            from unstructured.partition.auto import partition
            return True
        except ImportError:
            logger.warning("unstructured not installed. Install with: pip install unstructured[all-docs]")
            return False

    def _check_azure(self) -> bool:
        """Check if Azure Document Intelligence is configured."""
        if not self.azure_endpoint or not self.azure_key:
            logger.info("Azure Document Intelligence not configured")
            return False
        try:
            from azure.ai.formrecognizer import DocumentAnalysisClient
            return True
        except ImportError:
            logger.warning("azure-ai-formrecognizer not installed")
            return False

    def _get_document_type(self, filename: str) -> DocumentType:
        """Determine document type from filename."""
        ext = Path(filename).suffix.lower().lstrip(".")

        type_map = {
            "pdf": DocumentType.PDF,
            "docx": DocumentType.DOCX,
            "doc": DocumentType.DOC,
            "xlsx": DocumentType.XLSX,
            "xls": DocumentType.XLS,
            "pptx": DocumentType.PPTX,
            "txt": DocumentType.TXT,
            "csv": DocumentType.CSV,
            "png": DocumentType.IMAGE,
            "jpg": DocumentType.IMAGE,
            "jpeg": DocumentType.IMAGE,
            "tiff": DocumentType.IMAGE,
            "tif": DocumentType.IMAGE,
            "bmp": DocumentType.IMAGE,
        }

        return type_map.get(ext, DocumentType.UNKNOWN)

    def _calculate_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of document content."""
        return hashlib.sha256(content).hexdigest()

    def _should_use_azure(
        self,
        file_size: int,
        doc_type: DocumentType,
        is_scanned: bool = False,
    ) -> bool:
        """
        Determine if Azure should be used based on heuristics.

        Uses Azure for:
        - Scanned PDFs
        - Large files (>5MB)
        - Images
        """
        if not self._azure_available:
            return False

        # Always use Azure for images
        if doc_type == DocumentType.IMAGE:
            return True

        # Use Azure for large files
        if file_size > self.AZURE_SIZE_THRESHOLD:
            return True

        # Use Azure for scanned documents
        if is_scanned:
            return True

        return False

    async def extract(
        self,
        file_path: Optional[str] = None,
        file_content: Optional[bytes] = None,
        filename: Optional[str] = None,
        force_engine: Optional[ExtractionEngine] = None,
    ) -> ExtractionResult:
        """
        Extract text and structure from a document.

        Args:
            file_path: Path to document file
            file_content: Document content as bytes
            filename: Original filename (required if using file_content)
            force_engine: Force specific extraction engine

        Returns:
            ExtractionResult with extracted content and metadata
        """
        import time
        start_time = time.time()

        # Validate inputs
        if file_path is None and file_content is None:
            raise ValueError("Either file_path or file_content must be provided")

        if file_content is not None and filename is None:
            raise ValueError("filename required when using file_content")

        # Get file info
        if file_path:
            path = Path(file_path)
            filename = filename or path.name
            with open(path, "rb") as f:
                content = f.read()
        else:
            content = file_content

        file_hash = self._calculate_hash(content)
        file_size = len(content)
        doc_type = self._get_document_type(filename)

        logger.info(f"Extracting {filename} ({file_size} bytes, type={doc_type.value})")

        # Select extraction engine
        if force_engine:
            engine = force_engine
        elif self._should_use_azure(file_size, doc_type):
            engine = ExtractionEngine.AZURE_DOCUMENT_INTELLIGENCE
        elif self._unstructured_available:
            engine = ExtractionEngine.UNSTRUCTURED
        else:
            engine = ExtractionEngine.FALLBACK_TEXT

        # Extract based on engine
        try:
            if engine == ExtractionEngine.UNSTRUCTURED:
                result = await self._extract_with_unstructured(content, filename, doc_type)
            elif engine == ExtractionEngine.AZURE_DOCUMENT_INTELLIGENCE:
                result = await self._extract_with_azure(content, filename, doc_type)
            else:
                result = await self._extract_fallback(content, filename, doc_type)
        except Exception as e:
            logger.error(f"Extraction failed with {engine.value}: {e}")
            # Try fallback
            if engine != ExtractionEngine.FALLBACK_TEXT:
                logger.info("Attempting fallback extraction")
                result = await self._extract_fallback(content, filename, doc_type)
                result.warnings.append(f"Primary extraction failed: {str(e)}")
            else:
                raise

        # Add metadata
        extraction_time = (time.time() - start_time) * 1000
        result.filename = filename
        result.file_hash = file_hash
        result.file_size_bytes = file_size
        result.document_type = doc_type
        result.engine_used = engine
        result.extraction_time_ms = extraction_time
        result.extracted_at = datetime.utcnow()

        logger.info(
            f"Extraction complete: {len(result.full_text)} chars, "
            f"{len(result.elements)} elements, {len(result.tables)} tables, "
            f"{extraction_time:.1f}ms"
        )

        return result

    async def _extract_with_unstructured(
        self,
        content: bytes,
        filename: str,
        doc_type: DocumentType,
    ) -> ExtractionResult:
        """Extract using unstructured library."""
        from unstructured.partition.auto import partition

        # Write to temp file for unstructured
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Partition document
            elements = partition(filename=tmp_path)

            # Process elements
            extracted_elements = []
            tables = []
            full_text_parts = []
            page_count = 0

            for elem in elements:
                # Get element type
                elem_type = type(elem).__name__
                text = str(elem)

                # Track page numbers
                page_num = getattr(elem.metadata, "page_number", None)
                if page_num and page_num > page_count:
                    page_count = page_num

                # Extract coordinates if available
                coords = None
                if hasattr(elem.metadata, "coordinates"):
                    c = elem.metadata.coordinates
                    if c:
                        coords = {
                            "x1": c.points[0][0] if c.points else None,
                            "y1": c.points[0][1] if c.points else None,
                            "x2": c.points[2][0] if len(c.points) > 2 else None,
                            "y2": c.points[2][1] if len(c.points) > 2 else None,
                        }

                # Handle tables specially
                if elem_type == "Table":
                    # Try to get table structure
                    if hasattr(elem, "metadata") and hasattr(elem.metadata, "text_as_html"):
                        tables.append(self._parse_html_table(elem.metadata.text_as_html, page_num))

                extracted_elements.append(ExtractedElement(
                    element_type=elem_type,
                    text=text,
                    page_number=page_num,
                    coordinates=coords,
                    confidence=1.0,
                ))

                full_text_parts.append(text)

            # Detect if scanned
            is_scanned = self._detect_scanned(extracted_elements, doc_type)

            return ExtractionResult(
                filename=filename,
                file_hash="",  # Will be set later
                document_type=doc_type,
                file_size_bytes=0,  # Will be set later
                page_count=page_count or 1,
                engine_used=ExtractionEngine.UNSTRUCTURED,
                extraction_time_ms=0,  # Will be set later
                extracted_at=datetime.utcnow(),
                full_text="\n\n".join(full_text_parts),
                elements=extracted_elements,
                tables=tables,
                confidence_score=0.95,
                is_scanned=is_scanned,
                ocr_applied=is_scanned,
            )

        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass

    async def _extract_with_azure(
        self,
        content: bytes,
        filename: str,
        doc_type: DocumentType,
    ) -> ExtractionResult:
        """Extract using Azure Document Intelligence."""
        from azure.ai.formrecognizer import DocumentAnalysisClient
        from azure.core.credentials import AzureKeyCredential

        client = DocumentAnalysisClient(
            endpoint=self.azure_endpoint,
            credential=AzureKeyCredential(self.azure_key),
        )

        # Use prebuilt-document model for general extraction
        poller = client.begin_analyze_document("prebuilt-document", content)
        result = poller.result()

        # Process results
        extracted_elements = []
        tables = []
        full_text_parts = []

        # Extract paragraphs
        for para in result.paragraphs or []:
            extracted_elements.append(ExtractedElement(
                element_type="paragraph",
                text=para.content,
                page_number=para.bounding_regions[0].page_number if para.bounding_regions else None,
                confidence=para.confidence or 1.0,
            ))
            full_text_parts.append(para.content)

        # Extract tables
        for table in result.tables or []:
            headers = []
            rows = []
            current_row = []
            current_row_idx = 0

            for cell in table.cells:
                if cell.row_index == 0:
                    headers.append(cell.content)
                else:
                    if cell.row_index != current_row_idx:
                        if current_row:
                            rows.append(current_row)
                        current_row = []
                        current_row_idx = cell.row_index
                    current_row.append(cell.content)

            if current_row:
                rows.append(current_row)

            tables.append(TableData(
                headers=headers,
                rows=rows,
                page_number=table.bounding_regions[0].page_number if table.bounding_regions else None,
                confidence=table.confidence or 1.0,
            ))

        return ExtractionResult(
            filename=filename,
            file_hash="",
            document_type=doc_type,
            file_size_bytes=0,
            page_count=len(result.pages) if result.pages else 1,
            engine_used=ExtractionEngine.AZURE_DOCUMENT_INTELLIGENCE,
            extraction_time_ms=0,
            extracted_at=datetime.utcnow(),
            full_text="\n\n".join(full_text_parts),
            elements=extracted_elements,
            tables=tables,
            confidence_score=0.9,
            is_scanned=True,  # If we're using Azure, assume scanned
            ocr_applied=True,
        )

    async def _extract_fallback(
        self,
        content: bytes,
        filename: str,
        doc_type: DocumentType,
    ) -> ExtractionResult:
        """Fallback extraction for when primary engines fail."""
        text = ""
        warnings = ["Using fallback text extraction - limited accuracy"]

        try:
            # Try to decode as text
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except:
                text = f"[Unable to extract text from {filename}]"
                warnings.append("Binary content could not be decoded")

        return ExtractionResult(
            filename=filename,
            file_hash="",
            document_type=doc_type,
            file_size_bytes=0,
            page_count=1,
            engine_used=ExtractionEngine.FALLBACK_TEXT,
            extraction_time_ms=0,
            extracted_at=datetime.utcnow(),
            full_text=text,
            elements=[ExtractedElement(
                element_type="text",
                text=text,
                confidence=0.5,
            )],
            tables=[],
            confidence_score=0.5,
            is_scanned=False,
            ocr_applied=False,
            warnings=warnings,
        )

    def _detect_scanned(
        self,
        elements: List[ExtractedElement],
        doc_type: DocumentType,
    ) -> bool:
        """
        Detect if document is scanned (image-based).

        Heuristic: If text density is very low relative to page count,
        the document is likely scanned.
        """
        if doc_type == DocumentType.IMAGE:
            return True

        if not elements:
            return True

        # Check for OCR indicators
        for elem in elements:
            if "ocr" in elem.element_type.lower():
                return True

        # Low confidence on text elements suggests OCR
        avg_confidence = sum(e.confidence for e in elements) / len(elements)
        if avg_confidence < 0.8:
            return True

        return False

    def _parse_html_table(
        self,
        html: str,
        page_num: Optional[int],
    ) -> TableData:
        """Parse HTML table string into TableData."""
        # Simple HTML table parser
        headers = []
        rows = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Get headers
            header_row = soup.find("tr")
            if header_row:
                for th in header_row.find_all(["th", "td"]):
                    headers.append(th.get_text(strip=True))

            # Get data rows
            for tr in soup.find_all("tr")[1:]:
                row = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if row:
                    rows.append(row)

        except ImportError:
            # Fallback: basic regex parsing
            import re
            cells = re.findall(r"<t[hd][^>]*>([^<]*)</t[hd]>", html, re.IGNORECASE)
            if cells:
                # Assume first few are headers
                headers = cells[:5]
                # Rest are data
                for i in range(5, len(cells), len(headers)):
                    rows.append(cells[i:i+len(headers)])

        return TableData(
            headers=headers,
            rows=rows,
            page_number=page_num,
            confidence=0.9,
        )


# Global extractor instance
_extractor: Optional[DocumentExtractor] = None


def get_document_extractor() -> DocumentExtractor:
    """Get or create global document extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = DocumentExtractor()
    return _extractor
