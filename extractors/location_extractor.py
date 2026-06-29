import re


def extract_locations(document):
    locations = []
    seen = set()
    
    text = document.get('text', '')
    structured_data = document.get('structured_data')
    entities = document.get('entities', [])
    path = document.get('path', '')
    
    # Extract from location entities
    for entity in entities:
        if entity.get('type') == 'location':
            location_name = entity.get('value', '')
            if location_name and location_name not in seen:
                locations.append({
                    'name': location_name,
                    'latitude': None,
                    'longitude': None,
                    'source': path
                })
                seen.add(location_name)
    
    # Extract GPS coordinates from structured_data (EXIF, etc.)
    if structured_data:
        _extract_gps_from_structured(structured_data, path, locations, seen)
    
    # Extract latitude/longitude patterns from text
    _extract_coords_from_text(text, path, locations, seen)
    
    return locations


def _extract_gps_from_structured(data, source, locations, seen):
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check for GPS-related keys
            if 'gps' in key_lower or 'latitude' in key_lower or 'longitude' in key_lower:
                if isinstance(value, (int, float)):
                    _process_gps_value(key, value, data, source, locations, seen)
            
            # Recurse into nested structures
            elif isinstance(value, (dict, list)):
                _extract_gps_from_structured(value, source, locations, seen)
    
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                _extract_gps_from_structured(item, source, locations, seen)


def _process_gps_value(key, value, data, source, locations, seen):
    key_lower = key.lower()
    latitude = None
    longitude = None
    name = None
    
    if 'latitude' in key_lower:
        latitude = value
        longitude = data.get('longitude') or data.get('Longitude')
        name = f"Lat: {latitude}, Lon: {longitude}" if longitude else f"Lat: {latitude}"
    elif 'longitude' in key_lower:
        longitude = value
        latitude = data.get('latitude') or data.get('Latitude')
        name = f"Lat: {latitude}, Lon: {longitude}" if latitude else f"Lon: {longitude}"
    elif 'gps' in key_lower:
        # Try to find lat/lon from siblings
        if isinstance(data, dict):
            lat = data.get('GPSLatitude') or data.get('latitude') or data.get('Lat')
            lon = data.get('GPSLongitude') or data.get('longitude') or data.get('Lon')
            if lat is not None and lon is not None:
                latitude = lat
                longitude = lon
                name = f"GPS: {latitude}, {longitude}"
    
    if latitude is not None or longitude is not None:
        location_key = (latitude, longitude)
        if location_key not in seen:
            locations.append({
                'name': name,
                'latitude': latitude,
                'longitude': longitude,
                'source': source
            })
            seen.add(location_key)


def _extract_coords_from_text(text, source, locations, seen):
    # Pattern for GPS coordinates like "40.7128° N, 74.0060° W" or "40.7128, -74.0060"
    # Must have decimal precision of at least 4 digits to avoid matching dates like "1, 2025"
    coord_patterns = [
        # Decimal degree format with direction (e.g., "40.7128° N, 74.0060° W")
        r'(-?\d{2,}\.\d+)\s*[°]?\s*[NS]?\s*[,\s]\s*(-?\d{2,}\.\d+)\s*[°]?\s*[EW]?',
        # Latitude/Longitude labels
        r'latitude[:\s]+(-?\d{2,}\.\d+)[,\s]+longitude[:\s]+(-?\d{2,}\.\d+)',
        r'lat[:\s]+(-?\d{2,}\.\d+)[,\s]+lon[g]?[:\s]+(-?\d{2,}\.\d+)',
        # GPS bracket format
        r'GPS[:\s]+\[?\s*(-?\d{2,}\.\d+)\s*,\s*(-?\d{2,}\.\d+)\s*\]?',
        # Decimal degrees without direction (requires 2+ decimal places)
        r'\b(-?\d{2,}\.\d{2,})\s*,\s*(-?\d{2,}\.\d{2,})\b',
    ]
    
    for pattern in coord_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                
                # Validate lat/lon ranges
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    location_key = (lat, lon)
                    if location_key not in seen:
                        locations.append({
                            'name': f"Coordinates: {lat}, {lon}",
                            'latitude': lat,
                            'longitude': lon,
                            'source': source
                        })
                        seen.add(location_key)
            except (ValueError, IndexError):
                continue
    
    # Extract city/location names from text
    _extract_named_locations(text, source, locations, seen)


def _extract_named_locations(text, source, locations, seen):
    """Extract named locations like cities and countries from text."""
    import re
    
    # Major cities and countries to look for
    known_locations = [
        'Manila', 'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
        'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose',
        'London', 'Paris', 'Tokyo', 'Beijing', 'Shanghai', 'Mumbai', 'Delhi',
        'Sydney', 'Melbourne', 'Toronto', 'Vancouver', 'Berlin', 'Madrid',
        'Rome', 'Amsterdam', 'Brussels', 'Vienna', 'Prague', 'Moscow',
        'Dubai', 'Singapore', 'Hong Kong', 'Seoul', 'Bangkok', 'Kuala Lumpur',
        'Jakarta', 'Manila', 'Cebu', 'Istanbul', 'Cairo', 'Johannesburg',
        'Cape Town', 'Lagos', 'Nairobi', 'Casablanca', 'Buenos Aires',
        'Sao Paulo', 'Mexico City', 'Lima', 'Bogota', 'Santiago',
    ]
    
    # Country names
    countries = [
        'Philippines', 'United States', 'USA', 'Canada', 'Mexico', 'Brazil',
        'Argentina', 'Chile', 'Colombia', 'Peru', 'United Kingdom', 'UK',
        'France', 'Germany', 'Spain', 'Italy', 'Netherlands', 'Belgium',
        'Austria', 'Switzerland', 'Poland', 'Czech Republic', 'Czechia',
        'Hungary', 'Romania', 'Bulgaria', 'Greece', 'Turkey', 'Russia',
        'Ukraine', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Ireland',
        'Portugal', 'China', 'Japan', 'South Korea', 'India', 'Thailand',
        'Vietnam', 'Indonesia', 'Malaysia', 'Singapore', 'Australia',
        'New Zealand', 'South Africa', 'Egypt', 'Nigeria', 'Kenya',
        'Morocco', 'Israel', 'Saudi Arabia', 'UAE', 'United Arab Emirates',
        'Qatar', 'Kuwait', 'Iran', 'Iraq', 'Pakistan', 'Bangladesh',
    ]
    
    # Extract known locations
    text_lower = text.lower()
    
    for location in known_locations:
        # Word boundary match
        pattern = r'\b' + re.escape(location) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            location_key = location.lower()
            if location_key not in seen:
                seen.add(location_key)
                locations.append({
                    'name': location,
                    'latitude': None,
                    'longitude': None,
                    'source': source,
                    'type': 'CITY'
                })
    
    for country in countries:
        pattern = r'\b' + re.escape(country) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            location_key = country.lower()
            if location_key not in seen:
                seen.add(location_key)
                locations.append({
                    'name': country,
                    'latitude': None,
                    'longitude': None,
                    'source': source,
                    'type': 'COUNTRY'
                })