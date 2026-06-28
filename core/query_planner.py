import re


def plan_query(question):
    question_lower = question.lower()
    
    # Default structure
    plan = {
        "intent": "unknown",
        "required_evidence": [],
        "filters": {}
    }
    
    # Extract dates
    dates = extract_dates(question)
    if dates:
        plan["filters"]["dates"] = dates
    
    # Extract entity names
    entities = extract_entity_names(question)
    if entities:
        plan["filters"]["entities"] = entities
    
    # Pattern matching for intents
    if "where was" in question_lower:
        plan["intent"] = "location_query"
        plan["required_evidence"] = ["events", "locations", "images"]
    
    elif "what happened" in question_lower:
        plan["intent"] = "timeline_query"
        plan["required_evidence"] = ["events", "documents"]
    
    elif "show me everything related to" in question_lower:
        plan["intent"] = "entity_query"
        plan["required_evidence"] = ["entities", "documents", "events"]
    
    elif "profile of" in question_lower:
        plan["intent"] = "profile_query"
        plan["required_evidence"] = ["entities", "relationships", "events", "documents"]
    
    elif "when did" in question_lower:
        plan["intent"] = "event_query"
        plan["required_evidence"] = ["events"]
    
    return plan


def extract_dates(text):
    dates = []
    
    # ISO format: YYYY-MM-DD
    iso_pattern = r'\b(\d{4}-\d{2}-\d{2})\b'
    for match in re.finditer(iso_pattern, text):
        dates.append(match.group(1))
    
    # Month name formats: "January 1 2026", "Jan 1, 2026"
    month_names = 'January|February|March|April|May|June|July|August|September|October|November|December'
    month_abbr = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'
    
    month_pattern = rf'\b(?:{month_names}|{month_abbr})\s+\d{{1,2}},?\s+\d{{4}}\b'
    for match in re.finditer(month_pattern, text, re.IGNORECASE):
        dates.append(match.group())
    
    # MM/DD/YYYY format
    slash_pattern = r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b'
    for match in re.finditer(slash_pattern, text):
        dates.append(match.group())
    
    # Month Year format: "January 2026"
    month_year_pattern = rf'\b(?:{month_names}|{month_abbr})\s+\d{{4}}\b'
    for match in re.finditer(month_year_pattern, text, re.IGNORECASE):
        dates.append(match.group())
    
    return dates


def extract_entity_names(text):
    entities = []
    
    # Capitalized words that appear to be names/entities
    # Pattern: Capitalized words not at start of sentence, potentially multi-word
    name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
    for match in re.finditer(name_pattern, text):
        entities.append(match.group())
    
    # Quoted strings
    quoted_pattern = r'"([^"]+)"'
    for match in re.finditer(quoted_pattern, text):
        entities.append(match.group(1))
    
    # All caps acronyms (3+ letters)
    acronym_pattern = r'\b([A-Z]{3,})\b'
    for match in re.finditer(acronym_pattern, text):
        entities.append(match.group())
    
    return entities