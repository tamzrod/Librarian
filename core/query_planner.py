import re


def plan_query(question):
    question_lower = question.lower()
    
    plan = {
        "intent": "unknown",
        "required_evidence": [],
        "filters": {},
        "confidence": 0.5
    }
    
    # Pattern matching for intents
    if "where was" in question_lower:
        plan["intent"] = "location_query"
        plan["required_evidence"] = ["events", "locations", "documents"]
        plan["confidence"] = 0.95
    
    elif "what happened" in question_lower:
        plan["intent"] = "timeline_query"
        plan["required_evidence"] = ["events", "documents"]
        plan["confidence"] = 0.90
    
    elif "show me everything related to" in question_lower:
        plan["intent"] = "entity_query"
        plan["required_evidence"] = ["entities", "documents", "events"]
        plan["confidence"] = 0.95
        # Extract entity after "related to"
        entity = extract_entity_after_phrase(question, "show me everything related to")
        if entity:
            plan["filters"]["entity"] = entity
    
    elif "profile of" in question_lower:
        plan["intent"] = "profile_query"
        plan["required_evidence"] = ["entities", "relationships", "events", "documents"]
        plan["confidence"] = 0.95
        # Extract entity after "profile of"
        entity = extract_entity_after_phrase(question, "profile of")
        if entity:
            plan["filters"]["entity"] = entity
    
    elif "when did" in question_lower:
        plan["intent"] = "event_query"
        plan["required_evidence"] = ["events"]
        plan["confidence"] = 0.90
    
    elif any(phrase in question_lower for phrase in ["find ", "show ", "list "]):
        plan["intent"] = "document_query"
        plan["required_evidence"] = ["documents"]
        plan["confidence"] = 0.75
    
    else:
        plan["intent"] = "unknown"
        plan["required_evidence"] = []
        plan["confidence"] = 0.5
    
    # Extract date filters
    date_filter = extract_date_filter(question)
    if date_filter:
        plan["filters"].update(date_filter)
    
    return plan


def extract_date_filter(text):
    month_names = 'January|February|March|April|May|June|July|August|September|October|November|December'
    month_abbr = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'
    
    # ISO format: 2026-01-01
    iso_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if iso_match:
        return {"date": iso_match.group(1)}
    
    # Full date: "January 1 2026" or "Jan 1, 2026"
    full_date_pattern = rf'\b((?:{month_names}|{month_abbr})\s+\d{{1,2}},?\s+\d{{4}})\b'
    full_match = re.search(full_date_pattern, text, re.IGNORECASE)
    if full_match:
        return {"date": full_match.group(1)}
    
    # Month only: "January 2026" or "Jan 2026"
    month_year_pattern = rf'\b((?:{month_names}|{month_abbr})\s+\d{{4}})\b'
    month_match = re.search(month_year_pattern, text, re.IGNORECASE)
    if month_match:
        month_str = month_match.group(1)
        # Convert to YYYY-MM format
        month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
            'oct': '10', 'nov': '11', 'dec': '12'
        }
        parts = month_str.lower().split()
        if len(parts) == 2:
            month_num = month_map.get(parts[0], '01')
            year = parts[1]
            return {"month": f"{year}-{month_num}"}
    
    return {}


def extract_entity_after_phrase(text, phrase):
    question_lower = text.lower()
    idx = question_lower.find(phrase)
    if idx == -1:
        return None
    
    # Get everything after the phrase
    after = text[idx + len(phrase):].strip()
    # Remove trailing punctuation
    after = re.sub(r'[?!.]$', '', after)
    # Take up to next punctuation or 50 chars
    match = re.match(r'^[^?!.,]+', after)
    if match:
        return match.group().strip()
    return after if after else None