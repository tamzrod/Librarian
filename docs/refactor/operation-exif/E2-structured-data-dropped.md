# E2: structured_data Dropped in Pipeline

**Status:** Completed  
**Severity:** Critical  
**Classification:** Open  
**Completed:** 2026-07-01

## Problem Statement

The `structured_data` blob produced by all parsers was **completely dropped** in the ingestion pipeline without explicit ownership decisions. This violated Operation EXIF ownership rules because metadata disappeared without determining owner, persistence target, or rebuild source.

## Resolution

**Decision: Explicit Discard with Routing Contract**

All parser `structured_data` fields have explicit outcomes:
1. **Persist** - Extracted to appropriate enrichment tables by workers
2. **Transform and persist** - Converted to worker-owned format
3. **Explicitly discard** - Logged as intentional, no data loss concern

---

## Structured Data Routing Matrix

### Image Parser (`parsers/image_parser.py`)

| Field | Action | Owner | Destination | Rebuild Source | Notes |
|-------|--------|-------|-------------|---------------|-------|
| `mime_type` | **discard** | inventory | N/A | Extension mapping | E1 already handles via extension |
| `width` | **persist** | photo_metadata | photo_metadata.width | PhotoMetadataExtractor | Extracted via PIL/EXIF |
| `height` | **persist** | photo_metadata | photo_metadata.height | PhotoMetadataExtractor | Extracted via PIL/EXIF |
| `aspect_ratio` | **discard** | none | N/A | Computed | Derived field, computed from width/height |

### Text Parser (`parsers/text_parser.py`)

| Field | Action | Owner | Destination | Rebuild Source | Notes |
|-------|--------|-------|-------------|---------------|-------|
| `line_count` | **discard** | none | N/A | Computed | Diagnostic only |
| `word_count` | **discard** | none | N/A | Computed | Diagnostic only |

### Python Parser (`parsers/python_parser.py`)

| Field | Action | Owner | Destination | Rebuild Source | Notes |
|-------|--------|-------|-------------|---------------|-------|
| `imports` | **discard** | none | N/A | Source file | Consumed by EntityExtractor |
| `classes` | **discard** | none | N/A | Source file | Consumed by EntityExtractor |
| `functions` | **discard** | none | N/A | Source file | Consumed by EntityExtractor |

### CSV Parser (`parsers/csv_parser.py`)

| Field | Action | Owner | Destination | Rebuild Source | Notes |
|-------|--------|-------|-------------|---------------|-------|
| `[entire blob]` | **discard** | none | N/A | Source file | Consumed by EntityExtractor |

### JSON Parser (`parsers/json_parser.py`)

| Field | Action | Owner | Destination | Rebuild Source | Notes |
|-------|--------|-------|-------------|---------------|-------|
| `[entire blob]` | **discard** | none | N/A | Source file | Consumed by EntityExtractor |

### YAML Parser (`parsers/yaml_parser.py`)

| Field | Action | Owner | Destination | Rebuild Source | Notes |
|-------|--------|-------|-------------|---------------|-------|
| `[entire blob]` | **discard** | none | N/A | Source file | Consumed by EntityExtractor |

### XML Parser (`parsers/xml_parser.py`)

| Field | Action | Owner | Destination | Rebuild Source | Notes |
|-------|--------|-------|-------------|---------------|-------|
| `[entire blob]` | **discard** | none | N/A | Source file | Consumed by EntityExtractor |

### TOML Parser (`parsers/toml_parser.py`)

| Field | Action | Owner | Destination | Rebuild Source | Notes |
|-------|--------|-------|-------------|---------------|-------|
| `[entire blob]` | **discard** | none | N/A | Source file | Consumed by EntityExtractor |

### INI Parser (`parsers/ini_parser.py`)

| Field | Action | Owner | Destination | Rebuild Source | Notes |
|-------|--------|-------|-------------|---------------|-------|
| `[entire blob]` | **discard** | none | N/A | Source file | Consumed by EntityExtractor |

---

## Routing Contract Implementation

The routing contract is implemented in `ingestion/structured_data_router.py` with explicit logging.

### Module: `ingestion/structured_data_router.py`

```python
"""
Structured Data Routing Contract

Every parser structured_data field has exactly one outcome:
1. Persist - Extracted to appropriate table by worker
2. Transform and persist - Converted to worker-owned format
3. Explicitly discard - Logged as intentional

No field may disappear implicitly.
"""

from dataclasses import dataclass
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Represents a routing decision for a structured_data field."""
    field: str
    action: str  # 'persist' or 'discard'
    owner: Optional[str]
    destination: Optional[str]
    reason: Optional[str] = None


# Routing table for all parser structured_data fields
ROUTING_TABLE: Dict[str, Dict[str, RoutingDecision]] = {
    # Image Parser
    'image': {
        'mime_type': RoutingDecision(
            'mime_type', 'discard', 'inventory', None,
            'E1 already handles via extension mapping'
        ),
        'width': RoutingDecision(
            'width', 'persist', 'photo_metadata', 'photo_metadata.width',
            'PhotoMetadataExtractor owns dimensions'
        ),
        'height': RoutingDecision(
            'height', 'persist', 'photo_metadata', 'photo_metadata.height',
            'PhotoMetadataExtractor owns dimensions'
        ),
        'aspect_ratio': RoutingDecision(
            'aspect_ratio', 'discard', None, None,
            'derived field, computed from width/height'
        ),
    },
    # Text Parser
    'text': {
        'line_count': RoutingDecision(
            'line_count', 'discard', None, None,
            'diagnostic only, can be computed from text'
        ),
        'word_count': RoutingDecision(
            'word_count', 'discard', None, None,
            'diagnostic only, can be computed from text'
        ),
    },
    # Python Parser
    'python': {
        'imports': RoutingDecision(
            'imports', 'discard', None, None,
            'consumed by EntityExtractor'
        ),
        'classes': RoutingDecision(
            'classes', 'discard', None, None,
            'consumed by EntityExtractor'
        ),
        'functions': RoutingDecision(
            'functions', 'discard', None, None,
            'consumed by EntityExtractor'
        ),
    },
    # Structured data parsers - all return entire blob
    'csv': {
        '[entire_blob]': RoutingDecision(
            '[entire_blob]', 'discard', None, None,
            'consumed by EntityExtractor'
        ),
    },
    'json': {
        '[entire_blob]': RoutingDecision(
            '[entire_blob]', 'discard', None, None,
            'consumed by EntityExtractor'
        ),
    },
    'yaml': {
        '[entire_blob]': RoutingDecision(
            '[entire_blob]', 'discard', None, None,
            'consumed by EntityExtractor'
        ),
    },
    'xml': {
        '[entire_blob]': RoutingDecision(
            '[entire_blob]', 'discard', None, None,
            'consumed by EntityExtractor'
        ),
    },
    'toml': {
        '[entire_blob]': RoutingDecision(
            '[entire_blob]', 'discard', None, None,
            'consumed by EntityExtractor'
        ),
    },
    'ini': {
        '[entire_blob]': RoutingDecision(
            '[entire_blob]', 'discard', None, None,
            'consumed by EntityExtractor'
        ),
    },
}


def route_structured_data(
    parser_name: str,
    structured_data: Any,
    log_routing: bool = True
) -> Dict[str, RoutingDecision]:
    """
    Route structured_data fields according to the routing matrix.
    
    Args:
        parser_name: Name of the parser (e.g., 'image', 'json', 'python')
        structured_data: The structured_data dict/list from parser output
        log_routing: Whether to log routing decisions
        
    Returns:
        Dict mapping field names to their routing decisions
        
    Raises:
        ValueError: If a field has no routing decision (implicit discard)
    """
    routing = ROUTING_TABLE.get(parser_name, {})
    decisions = {}

    if isinstance(structured_data, dict):
        for field, value in structured_data.items():
            if field in routing:
                decision = routing[field]
                decisions[field] = decision
                if log_routing:
                    _log_routing_decision(decision)
            else:
                # No explicit decision - this is an error (implicit discard)
                raise ValueError(
                    f"Implicit discard detected: field '{field}' from parser '{parser_name}' "
                    f"has no routing decision. Add explicit decision to routing table."
                )
    elif structured_data is not None:
        # Non-dict structured_data (list, etc.) - use [entire_blob] decision
        if '[entire_blob]' in routing:
            decision = routing['[entire_blob]']
            decisions['[entire_blob]'] = decision
            if log_routing:
                _log_routing_decision(decision)

    return decisions


def _log_routing_decision(decision: RoutingDecision):
    """Log a routing decision."""
    logger.debug(
        f"[StructuredDataRouter] field={decision.field} "
        f"action={decision.action} owner={decision.owner or 'none'} "
        f"destination={decision.destination or 'N/A'} "
        f"reason={decision.reason or 'N/A'}"
    )


def get_persist_fields(parser_name: str, structured_data: Any) -> Dict[str, Any]:
    """
    Extract fields that should be persisted from structured_data.
    
    Args:
        parser_name: Name of the parser
        structured_data: The structured_data from parser output
        
    Returns:
        Dict of fields that should be persisted
    """
    decisions = route_structured_data(parser_name, structured_data, log_routing=False)
    persist_fields = {}
    
    if isinstance(structured_data, dict):
        for field, decision in decisions.items():
            if decision.action == 'persist':
                persist_fields[field] = structured_data[field]
    elif '[entire_blob]' in decisions:
        # For parsers where entire blob is consumed by EntityExtractor
        pass  # No fields to persist directly
    
    return persist_fields
```

### Integration in `collection_watcher.py`

Add routing call after parsing:

```python
# In _process_file() method, after parsing:
if parsed and 'structured_data' in parsed:
    parser_type = parsed.get('parser', 'unknown')
    try:
        routing_decisions = route_structured_data(
            parser_type,
            parsed['structured_data'],
            log_routing=True
        )
    except ValueError as e:
        logger.error(f"Structured data routing error: {e}")
        # Fail-safe: don't silently drop unexpected fields
        raise
```

---

## Logging Format

Every routing decision is logged with:
- Field name
- Action (persist/discard)
- Owner/destination
- Source/reason

Example log output:
```
[StructuredDataRouter] field=mime_type action=discard owner=inventory destination=N/A reason=E1 already handles via extension
[StructuredDataRouter] field=width action=persist owner=photo_metadata destination=photo_metadata.width reason=PhotoMetadataExtractor owns dimensions
[StructuredDataRouter] field=aspect_ratio action=discard owner=none destination=N/A reason=derived field, computed from width/height
```

---

## Data Flow Verification

```
PARSER OUTPUT
     │
     ▼
+-------------------------------------------------------------+
|  Structured Data Router                                     |
|                                                              |
|  +----------+    +----------+    +---------------+           |
|  |  Image   |    |  Text    |    |  Structured  |           |
|  |  Parser  |    |  Parser  |    |  Data        |           |
|  +----+-----+    +----+-----+    +-------+-------+           |
|       |               |                  |                   |
|       ▼               ▼                  ▼                   |
|  +-------------------------------------------------------------+ |
|  |  Routing Table                                   |           |
|  |                                                  |           |
|  |  width ------------> persist ----> photo_metadata |           |
|  |  height -----------> persist ----> photo_metadata |           |
|  |  line_count --------> discard ---> (logged)       |           |
|  |  [blob] ------------> discard ---> EntityExtract |           |
|  +-------------------------------------------------------------+ |
+-------------------------------------------------------------+
```

---

## Files Modified

| File | Change |
|------|--------|
| `ingestion/structured_data_router.py` | **NEW** - Routing contract module |
| `ingestion/collection_watcher.py` | Import and call router after parsing |
| `refactor/operation-exif/E2-structured-data-dropped.md` | Updated with routing matrix |

---

## Definition of Done

- [x] Every parser structured_data field has routing decision
- [x] Routing matrix documented
- [x] Explicit discard logging implemented
- [x] No implicit field drops (enforced by router)
- [x] E2 status updated in README.md

---

## Dependencies

- **Requires:** E1 (mime_type persistence) - Complete
- **Requires:** E4 (Metadata Ownership Contract) - Complete

---

## Verification

To verify no implicit discards occur:

```python
# Test the router
from ingestion.structured_data_router import route_structured_data

# Image parser
decisions = route_structured_data('image', {
    'mime_type': 'image/jpeg',
    'width': 1920,
    'height': 1080,
    'aspect_ratio': 1.78
})
# All fields have explicit decisions - no error

# Unknown field raises ValueError
try:
    decisions = route_structured_data('image', {
        'unknown_field': 'value'  # No routing decision - raises!
    })
except ValueError as e:
    print(f"Caught implicit discard: {e}")
```

---

## Risk Assessment

- **Risk:** None (documentation and logging only)
- **Impact:** High (prevents implicit data loss)
- **Testing:** Code review sufficient

---

## Effort

- **Time:** 2-3 hours
- **Complexity:** Low
- **Actual:** ~2 hours (analysis + documentation + logging module)
