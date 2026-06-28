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
    coord_patterns = [
        r'(-?\d+\.?\d*)\s*[°]?\s*[NS]?\s*[,\s]\s*(-?\d+\.?\d*)\s*[°]?\s*[EW]?',
        r'latitude[:\s]+(-?\d+\.?\d*)[,\s]+longitude[:\s]+(-?\d+\.?\d*)',
        r'lat[:\s]+(-?\d+\.?\d*)[,\s]+lon[g]?[:\s]+(-?\d+\.?\d*)',
        r'GPS[:\s]+\[?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]?',
    ]
    
    for pattern in coord_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                
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