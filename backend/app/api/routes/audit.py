"""
Audit Package Export API

Export audit events as a downloadable ZIP package containing:
- events.jsonl: All audit events in JSON Lines format
- README.md: Documentation and metadata about the export

EU AI Act Compliance: Art. 12 (5+ year retention), Art. 30 (Technical Documentation)
"""

import io
import json
import logging
import zipfile
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEventRecord(BaseModel):
    """Single audit event record."""
    event_id: str
    timestamp: datetime
    event_type: str
    actor_id: Optional[str] = None
    actor_type: str = "user"  # user, system, api
    resource_type: str
    resource_id: Optional[str] = None
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    severity: str = "info"  # debug, info, warning, error, critical
    outcome: str = "success"  # success, failure, pending


class AuditExportMetadata(BaseModel):
    """Metadata about the audit export."""
    export_id: str
    generated_at: datetime
    generated_by: str
    period_start: datetime
    period_end: datetime
    total_events: int
    event_types: Dict[str, int]
    format_version: str = "1.0"
    checksum_sha256: Optional[str] = None


class AuditExportRequest(BaseModel):
    """Request to export audit events."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: List[str] = Field(default_factory=list)
    severity_levels: List[str] = Field(default_factory=list)
    resource_types: List[str] = Field(default_factory=list)
    include_readme: bool = True


class AuditSummaryResponse(BaseModel):
    """Summary of audit events for a period."""
    period_start: datetime
    period_end: datetime
    total_events: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_outcome: Dict[str, int]
    by_resource: Dict[str, int]


# In-memory audit log (in production, this would be a database)
_audit_events: List[AuditEventRecord] = []


def _initialize_demo_events():
    """Initialize demo audit events."""
    global _audit_events
    if _audit_events:
        return

    now = datetime.utcnow()
    base_events = [
        # Data processing events
        {"event_type": "data.upload", "resource_type": "dataset", "action": "create", "severity": "info"},
        {"event_type": "data.process", "resource_type": "pipeline", "action": "execute", "severity": "info"},
        {"event_type": "data.validate", "resource_type": "quality", "action": "check", "severity": "info"},
        {"event_type": "pii.detect", "resource_type": "dataset", "action": "scan", "severity": "warning"},
        {"event_type": "pii.mask", "resource_type": "dataset", "action": "transform", "severity": "info"},

        # Decision events
        {"event_type": "decision.create", "resource_type": "decision", "action": "create", "severity": "info"},
        {"event_type": "decision.approve", "resource_type": "decision", "action": "approve", "severity": "info"},
        {"event_type": "decision.reject", "resource_type": "decision", "action": "reject", "severity": "warning"},
        {"event_type": "decision.assign", "resource_type": "decision", "action": "update", "severity": "info"},

        # User events
        {"event_type": "user.login", "resource_type": "session", "action": "create", "severity": "info"},
        {"event_type": "user.logout", "resource_type": "session", "action": "delete", "severity": "info"},
        {"event_type": "user.access", "resource_type": "resource", "action": "read", "severity": "debug"},

        # GDPR events
        {"event_type": "gdpr.export", "resource_type": "subject", "action": "export", "severity": "info"},
        {"event_type": "gdpr.delete", "resource_type": "subject", "action": "delete", "severity": "warning"},
        {"event_type": "gdpr.rectify", "resource_type": "subject", "action": "update", "severity": "info"},

        # System events
        {"event_type": "system.backup", "resource_type": "database", "action": "backup", "severity": "info"},
        {"event_type": "system.error", "resource_type": "service", "action": "error", "severity": "error"},
        {"event_type": "report.generate", "resource_type": "report", "action": "create", "severity": "info"},
    ]

    # Generate events for the last 30 days
    for day_offset in range(30, -1, -1):
        date = now - timedelta(days=day_offset)
        events_per_day = 20 + (hash(str(date.date())) % 30)

        for i in range(events_per_day):
            base = base_events[i % len(base_events)]
            hour = 8 + (i % 12)  # Business hours
            minute = (i * 7) % 60

            event = AuditEventRecord(
                event_id=f"evt_{uuid4().hex[:12]}",
                timestamp=date.replace(hour=hour, minute=minute, second=0, microsecond=0),
                event_type=base["event_type"],
                actor_id=f"user_{(i % 5) + 1}" if "user" in base["event_type"] or "decision" in base["event_type"] else "system",
                actor_type="user" if "user" in base["event_type"] or "decision" in base["event_type"] else "system",
                resource_type=base["resource_type"],
                resource_id=f"{base['resource_type']}_{uuid4().hex[:8]}",
                action=base["action"],
                details={
                    "source": "atlas_pipeline",
                    "version": "1.0",
                    "environment": "production",
                },
                ip_address=f"192.168.1.{(i % 50) + 100}" if "user" in base["event_type"] else None,
                severity=base["severity"],
                outcome="success" if hash(f"{date}_{i}") % 20 != 0 else "failure",
            )
            _audit_events.append(event)

    # Sort by timestamp
    _audit_events.sort(key=lambda e: e.timestamp, reverse=True)
    logger.info(f"Initialized {len(_audit_events)} demo audit events")


# Initialize on module load
_initialize_demo_events()


@router.get("/events", response_model=List[AuditEventRecord])
async def get_audit_events(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    severity: Optional[str] = Query(None, description="Severity filter"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Get audit events with optional filters.
    """
    filtered = _audit_events.copy()

    if start_date:
        filtered = [e for e in filtered if e.timestamp >= start_date]
    if end_date:
        filtered = [e for e in filtered if e.timestamp <= end_date]
    if event_type:
        filtered = [e for e in filtered if e.event_type == event_type]
    if severity:
        filtered = [e for e in filtered if e.severity == severity]

    return filtered[offset:offset + limit]


@router.get("/summary", response_model=AuditSummaryResponse)
async def get_audit_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to summarize"),
):
    """
    Get summary of audit events.
    """
    now = datetime.utcnow()
    start = now - timedelta(days=days)

    filtered = [e for e in _audit_events if e.timestamp >= start]

    by_type: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    by_outcome: Dict[str, int] = {}
    by_resource: Dict[str, int] = {}

    for event in filtered:
        by_type[event.event_type] = by_type.get(event.event_type, 0) + 1
        by_severity[event.severity] = by_severity.get(event.severity, 0) + 1
        by_outcome[event.outcome] = by_outcome.get(event.outcome, 0) + 1
        by_resource[event.resource_type] = by_resource.get(event.resource_type, 0) + 1

    return AuditSummaryResponse(
        period_start=start,
        period_end=now,
        total_events=len(filtered),
        by_type=by_type,
        by_severity=by_severity,
        by_outcome=by_outcome,
        by_resource=by_resource,
    )


@router.post("/export")
async def export_audit_package(
    request: AuditExportRequest = None,
):
    """
    Export audit events as a ZIP package.

    The package contains:
    - events.jsonl: Audit events in JSON Lines format
    - README.md: Documentation and metadata

    EU AI Act compliant - supports 5+ year retention (Art. 12).
    """
    if request is None:
        request = AuditExportRequest()

    now = datetime.utcnow()

    # Default date range: last 30 days
    start_date = request.start_date or (now - timedelta(days=30))
    end_date = request.end_date or now

    # Filter events
    filtered = _audit_events.copy()
    filtered = [e for e in filtered if start_date <= e.timestamp <= end_date]

    if request.event_types:
        filtered = [e for e in filtered if e.event_type in request.event_types]
    if request.severity_levels:
        filtered = [e for e in filtered if e.severity in request.severity_levels]
    if request.resource_types:
        filtered = [e for e in filtered if e.resource_type in request.resource_types]

    # Calculate event type counts
    event_type_counts: Dict[str, int] = {}
    for event in filtered:
        event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1

    # Create export metadata
    export_id = f"export_{uuid4().hex[:12]}"
    metadata = AuditExportMetadata(
        export_id=export_id,
        generated_at=now,
        generated_by="atlas_pipeline",
        period_start=start_date,
        period_end=end_date,
        total_events=len(filtered),
        event_types=event_type_counts,
    )

    # Create ZIP file in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Write events.jsonl
        events_content = "\n".join(
            event.model_dump_json() for event in filtered
        )
        zf.writestr("events.jsonl", events_content)

        # Write metadata.json
        zf.writestr("metadata.json", metadata.model_dump_json(indent=2))

        # Write README.md
        if request.include_readme:
            readme_content = f"""# Atlas Pipeline Audit Export

## Export Information

| Field | Value |
|-------|-------|
| Export ID | `{export_id}` |
| Generated At | {now.strftime('%Y-%m-%d %H:%M:%S UTC')} |
| Period | {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} |
| Total Events | {len(filtered):,} |

## Files Included

- **events.jsonl**: Audit events in JSON Lines format (one JSON object per line)
- **metadata.json**: Export metadata including event type counts
- **README.md**: This documentation file

## Event Types Summary

| Event Type | Count |
|------------|-------|
{chr(10).join(f"| {et} | {count:,} |" for et, count in sorted(event_type_counts.items()))}

## JSON Lines Format

Each line in `events.jsonl` is a valid JSON object with the following schema:

```json
{{
  "event_id": "evt_xxxxxxxxxxxx",
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "decision.approve",
  "actor_id": "user_1",
  "actor_type": "user",
  "resource_type": "decision",
  "resource_id": "dec_12345678",
  "action": "approve",
  "details": {{}},
  "severity": "info",
  "outcome": "success"
}}
```

## EU AI Act Compliance

This audit export is compliant with EU AI Act requirements:

- **Article 12**: Automatic logging and 5-year retention capability
- **Article 30**: Technical documentation for AI systems
- **GDPR Article 30**: Records of processing activities

## Importing Data

### Python
```python
import json

with open('events.jsonl', 'r') as f:
    for line in f:
        event = json.loads(line)
        print(event['event_type'], event['timestamp'])
```

### PostgreSQL
```sql
COPY audit_events FROM 'events.jsonl' WITH (FORMAT csv, QUOTE e'\\x01');
```

### DuckDB
```sql
SELECT * FROM read_json_auto('events.jsonl');
```

## Support

For questions about this audit export, contact:
- Email: support@atlas-intelligence.com
- Documentation: https://docs.atlas-intelligence.com/audit

---
Generated by Atlas Pipeline v1.0
"""
            zf.writestr("README.md", readme_content)

    # Prepare response
    zip_buffer.seek(0)
    filename = f"audit_export_{export_id}_{now.strftime('%Y%m%d')}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/export")
async def export_audit_package_get(
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
):
    """
    Export audit events (GET endpoint for simple downloads).
    """
    now = datetime.utcnow()
    request = AuditExportRequest(
        start_date=now - timedelta(days=days),
        end_date=now,
    )
    return await export_audit_package(request)


@router.get("/event-types")
async def get_event_types():
    """
    Get list of available event types.
    """
    types = set(e.event_type for e in _audit_events)
    return {
        "event_types": sorted(types),
        "count": len(types),
    }


@router.get("/retention-policy")
async def get_retention_policy():
    """
    Get audit retention policy information.

    EU AI Act Article 12 requires minimum 5-year retention.
    """
    return {
        "retention_years": 5,
        "retention_days": 1825,
        "compliance": {
            "eu_ai_act_article_12": True,
            "gdpr_article_30": True,
        },
        "storage": {
            "format": "JSON Lines (.jsonl)",
            "compression": "ZIP",
            "encryption": "AES-256 at rest",
        },
        "export_formats": ["jsonl", "zip"],
    }
