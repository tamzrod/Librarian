"""
Test PostgreSQL filter generation.
This test demonstrates the SQL queries that would be generated.
"""

import re


def generate_search_events_sql(date=None, month=None, entity=None, event_type=None):
    """Simulate SQL generation for search_events."""
    conditions = []
    params = []
    
    if date:
        conditions.append("e.timestamp >= %s")
        conditions.append("e.timestamp < %s::date + INTERVAL '1 day'")
        params.append(date)
        params.append(date)
    
    if month:
        year, mon = month.split('-')
        start_date = f"{year}-{mon}-01"
        if mon == '12':
            next_month = f"{int(year) + 1}-01-01"
        else:
            next_month = f"{year}-{int(mon) + 1:02d}-01"
        conditions.append("e.timestamp >= %s")
        conditions.append("e.timestamp < %s")
        params.append(start_date)
        params.append(next_month)
    
    if entity:
        conditions.append("""
            EXISTS (
                SELECT 1 FROM document_events dev
                JOIN document_entities de ON dev.document_id = de.document_id
                JOIN entities ent ON de.entity_id = ent.id
                WHERE dev.event_id = e.id AND ent.value ILIKE %s
            )
        """)
        params.append(f"%{entity}%")
    
    if event_type:
        conditions.append("e.event_type = %s")
        params.append(event_type)
    
    sql = """
        SELECT e.id, e.timestamp, e.event_type, e.description
        FROM events e
    """
    
    if conditions:
        sql += " WHERE " + "\n                AND ".join(conditions)
    
    sql += " ORDER BY e.timestamp DESC LIMIT 100"
    
    return sql, params


def generate_search_entities_sql(entity_type=None, value=None):
    """Simulate SQL generation for search_entities."""
    conditions = []
    params = []
    
    if entity_type:
        conditions.append("e.type = %s")
        params.append(entity_type)
    
    if value:
        conditions.append("e.value ILIKE %s")
        params.append(f"%{value}%")
    
    sql = """
        SELECT e.id, e.type, e.value, e.normalized_value
        FROM entities e
    """
    
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    sql += " ORDER BY e.value LIMIT 100"
    
    return sql, params


def generate_search_documents_sql(query=None, entity=None, date=None, month=None, location=None):
    """Simulate SQL generation for search_documents."""
    conditions = []
    params = []
    
    if query:
        conditions.append("(d.path ILIKE %s OR d.extension ILIKE %s)")
        params.extend([f"%{query}%", f"%{query}%"])
    
    if entity:
        conditions.append("""
            EXISTS (
                SELECT 1 FROM document_entities de
                JOIN entities e ON de.entity_id = e.id
                WHERE de.document_id = d.id AND e.value ILIKE %s
            )
        """)
        params.append(f"%{entity}%")
    
    if date:
        conditions.append("d.modified_time::date = %s")
        params.append(date)
    
    if month:
        conditions.append("TO_CHAR(d.modified_time, 'YYYY-MM') = %s")
        params.append(month)
    
    if location:
        conditions.append("""
            EXISTS (
                SELECT 1 FROM document_locations dl
                JOIN locations l ON dl.location_id = l.id
                WHERE dl.document_id = d.id AND l.name ILIKE %s
            )
        """)
        params.append(f"%{location}%")
    
    sql = "SELECT d.id, d.path FROM documents d"
    
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    sql += " ORDER BY d.modified_time DESC LIMIT 100"
    
    return sql, params


def generate_search_locations_sql(date=None, month=None, entity=None, location_name=None):
    """Simulate SQL generation for search_locations."""
    conditions = []
    params = []
    
    if date:
        conditions.append("""
            EXISTS (
                SELECT 1 FROM document_locations dl
                JOIN documents d ON dl.document_id = d.id
                WHERE dl.location_id = l.id AND d.modified_time::date = %s
            )
        """)
        params.append(date)
    
    if month:
        conditions.append("""
            EXISTS (
                SELECT 1 FROM document_locations dl
                JOIN documents d ON dl.document_id = d.id
                WHERE dl.location_id = l.id AND TO_CHAR(d.modified_time, 'YYYY-MM') = %s
            )
        """)
        params.append(month)
    
    if entity:
        conditions.append("""
            EXISTS (
                SELECT 1 FROM document_locations dl
                JOIN document_entities de ON dl.document_id = de.document_id
                JOIN entities ent ON de.entity_id = ent.id
                WHERE dl.location_id = l.id AND ent.value ILIKE %s
            )
        """)
        params.append(f"%{entity}%")
    
    if location_name:
        conditions.append("l.name ILIKE %s")
        params.append(f"%{location_name}%")
    
    sql = "SELECT l.id, l.name, l.latitude, l.longitude FROM locations l"
    
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    sql += " ORDER BY l.name LIMIT 100"
    
    return sql, params


def generate_search_relationships_sql(entity=None, relationship_type=None):
    """Simulate SQL generation for search_relationships."""
    conditions = []
    params = []
    
    if entity:
        conditions.append("(r.from_entity ILIKE %s OR r.to_entity ILIKE %s)")
        params.extend([f"%{entity}%", f"%{entity}%"])
    
    if relationship_type:
        conditions.append("r.relationship_type = %s")
        params.append(relationship_type)
    
    sql = "SELECT id, from_entity, to_entity, relationship_type FROM relationships"
    
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    sql += " ORDER BY relationship_type LIMIT 100"
    
    return sql, params


def display_test(name, sql, params, mock_results=None):
    """Display test results."""
    print("=" * 70)
    print(f"TEST: {name}")
    print("=" * 70)
    print("\nGenerated SQL:")
    # Format the SQL for readability
    formatted_sql = re.sub(r'\s+', ' ', sql).strip()
    formatted_sql = re.sub(r'SELECT', '\n  SELECT', formatted_sql)
    formatted_sql = re.sub(r'FROM', '\n  FROM', formatted_sql)
    formatted_sql = re.sub(r'WHERE', '\n  WHERE', formatted_sql)
    formatted_sql = re.sub(r'AND', '\n    AND', formatted_sql)
    formatted_sql = re.sub(r'ORDER BY', '\n  ORDER BY', formatted_sql)
    print(formatted_sql)
    print("\nParameters:")
    for i, p in enumerate(params, 1):
        print(f"  ${i}: {repr(p)}")
    if mock_results:
        print("\nMock Results:")
        for r in mock_results:
            print(f"  - {r}")
    print()


if __name__ == "__main__":
    # Test 1: search_events with date filter
    sql, params = generate_search_events_sql(date="2026-01-01")
    display_test(
        "search_events(date='2026-01-01')",
        sql, params,
        mock_results=[
            {"timestamp": "2026-01-01", "event_type": "photo", "description": "Photo taken"}
        ]
    )
    
    # Test 2: search_events with month filter
    sql, params = generate_search_events_sql(month="2026-01")
    display_test(
        "search_events(month='2026-01')",
        sql, params,
        mock_results=[
            {"timestamp": "2026-01-01", "event_type": "photo", "description": "Photo taken"},
            {"timestamp": "2026-01-15", "event_type": "visit", "description": "Site visit"}
        ]
    )
    
    # Test 3: search_entities with value filter
    sql, params = generate_search_entities_sql(value="ABC Corp")
    display_test(
        "search_entities(value='ABC Corp')",
        sql, params,
        mock_results=[
            {"type": "organization", "value": "ABC Corp"}
        ]
    )
    
    # Test 4: search_documents with query and entity
    sql, params = generate_search_documents_sql(query="contract", entity="ABC Corp")
    display_test(
        "search_documents(query='contract', entity='ABC Corp')",
        sql, params,
        mock_results=[
            {"path": "abc_contract.pdf"}
        ]
    )
    
    # Test 5: search_locations with date filter
    sql, params = generate_search_locations_sql(date="2026-01-01")
    display_test(
        "search_locations(date='2026-01-01')",
        sql, params,
        mock_results=[
            {"name": "Manila", "latitude": 14.5995, "longitude": 120.9842}
        ]
    )
    
    # Test 6: search_relationships with entity filter
    sql, params = generate_search_relationships_sql(entity="ABC Corp")
    display_test(
        "search_relationships(entity='ABC Corp')",
        sql, params,
        mock_results=[
            {"from": "ABC Corp", "to": "Manila", "type": "located_in"}
        ]
    )
    
    # Test 7: Combined filters
    sql, params = generate_search_events_sql(date="2026-01-15", event_type="site_visit")
    display_test(
        "search_events(date='2026-01-15', event_type='site_visit')",
        sql, params,
        mock_results=[
            {"timestamp": "2026-01-15", "event_type": "site_visit", "description": "Site visit at Marikina"}
        ]
    )
    
    print("=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)