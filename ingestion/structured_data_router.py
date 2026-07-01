"""
Structured Data Routing Contract

Every parser structured_data field has exactly one outcome:
1. Persist - Extracted to appropriate table by worker
2. Transform and persist - Converted to worker-owned format
3. Explicitly discard - Logged as intentional

No field may disappear implicitly.

This module enforces the routing contract defined in Operation EXIF E2.
See: refactor/operation-exif/E2-structured-data-dropped.md
"""

from dataclasses import dataclass
from typing import Optional, Any, Dict, List
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
# Format: parser_name -> field_name -> RoutingDecision
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
    # Structured data parsers - CSV returns list, others return arbitrary dicts
    'csv': {
        '[entire_blob]': RoutingDecision(
            '[entire_blob]', 'discard', None, None,
            'consumed by EntityExtractor'
        ),
    },
    'json': {
        # JSON returns arbitrary dict structure - use wildcard
        '[any_key]': RoutingDecision(
            '[any_key]', 'discard', None, None,
            'consumed by EntityExtractor - keys are arbitrary'
        ),
    },
    'yaml': {
        # YAML returns arbitrary dict structure - use wildcard
        '[any_key]': RoutingDecision(
            '[any_key]', 'discard', None, None,
            'consumed by EntityExtractor - keys are arbitrary'
        ),
    },
    'xml': {
        # XML parsed to dict - use wildcard
        '[any_key]': RoutingDecision(
            '[any_key]', 'discard', None, None,
            'consumed by EntityExtractor - keys are arbitrary'
        ),
    },
    'toml': {
        # TOML returns arbitrary dict structure - use wildcard
        '[any_key]': RoutingDecision(
            '[any_key]', 'discard', None, None,
            'consumed by EntityExtractor - keys are arbitrary'
        ),
    },
    'ini': {
        # INI returns arbitrary dict structure (section: {key: value})
        '[any_key]': RoutingDecision(
            '[any_key]', 'discard', None, None,
            'consumed by EntityExtractor - keys are arbitrary'
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
                # Check if parser has wildcard routing (for arbitrary dict parsers)
                if '[any_key]' in routing:
                    decision = routing['[any_key]']
                    decisions[field] = decision
                    if log_routing:
                        logger.debug(
                            f"[StructuredDataRouter] field={decision.field} (wildcard) "
                            f"action={decision.action} owner={decision.owner or 'none'} "
                            f"reason={decision.reason or 'N/A'}"
                        )
                else:
                    # No explicit decision - this is an error (implicit discard)
                    logger.error(
                        f"Implicit discard detected: field '{field}' from parser '{parser_name}' "
                        f"has no routing decision. Add explicit decision to routing table."
                    )
                    raise ValueError(
                        f"Implicit discard detected: field '{field}' from parser '{parser_name}' "
                        f"has no routing decision. Add explicit decision to routing table."
                    )
    elif structured_data is not None:
        # Non-dict structured_data (list from CSV, etc.)
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

    This is used when a worker needs to extract persist-worthy fields
    from parser output (e.g., image dimensions -> PhotoMetadataExtractor).

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

    return persist_fields


def log_routing_summary(parser_name: str, structured_data: Any) -> List[str]:
    """
    Log a summary of all routing decisions for debugging.

    Args:
        parser_name: Name of the parser
        structured_data: The structured_data from parser output

    Returns:
        List of formatted routing decision strings
    """
    routing = ROUTING_TABLE.get(parser_name, {})
    summary = []

    if isinstance(structured_data, dict):
        for field, value in structured_data.items():
            if field in routing:
                decision = routing[field]
                summary.append(
                    f"field={decision.field} action={decision.action} "
                    f"owner={decision.owner or 'none'} destination={decision.destination or 'N/A'}"
                )
    elif structured_data is not None:
        if '[entire_blob]' in routing:
            decision = routing['[entire_blob]']
            summary.append(
                f"field=[entire_blob] action={decision.action} "
                f"owner={decision.owner or 'none'} destination={decision.destination or 'N/A'}"
            )

    # Log the summary
    for line in summary:
        logger.debug(f"[StructuredDataRouter] {line}")

    return summary
