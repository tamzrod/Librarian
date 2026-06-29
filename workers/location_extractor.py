"""
Location extraction handler for the worker.

Phase 4: Implements the extract_locations job type.

This extracts location references from document content.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LocationExtractor:
    """
    Extracts location references from document content.
    
    This is a job handler that can be registered with the Worker.
    It handles the 'extract_locations' job type.
    """
    
    def __init__(self, backend):
        """
        Initialize the location extractor.
        
        Args:
            backend: Storage backend
        """
        self.backend = backend
    
    def extract_locations(self, job: dict) -> dict:
        """
        Extract locations from a document.
        
        This is the job handler for 'extract_locations' jobs.
        
        Args:
            job: Job dict with document_id and job_type
            
        Returns:
            Dict with extraction results
        """
        document_id = job['document_id']
        job_id = job['id']
        
        logger.info(f"Starting location extraction for document {document_id}")
        
        try:
            # Get document content
            content_data = self.backend.get_content(document_id)
            
            if not content_data or not content_data.get('content'):
                raise ValueError(f"No content found for document {document_id}")
            
            content = content_data['content']
            logger.info(f"Extracting locations from {len(content)} chars of content")
            
            # Extract locations
            locations = self._extract_locations_from_text(content)
            
            # Save locations to database
            saved_count = self._save_locations(document_id, locations)
            
            logger.info(f"Successfully extracted {saved_count} locations from document {document_id}")
            
            return {
                'document_id': document_id,
                'locations_extracted': saved_count,
                'location_types': list(set(loc.get('location_type') for loc in locations if loc.get('location_type')))
            }
            
        except Exception as e:
            logger.error(f"Location extraction failed for document {document_id}: {e}")
            raise
    
    def _extract_locations_from_text(self, text: str) -> list:
        """
        Extract location references from text.
        
        Uses pattern-based extraction for common location formats.
        
        Args:
            text: Input text
            
        Returns:
            List of location dicts
        """
        locations = []
        import re
        
        # Try to use the real location extractor if available
        try:
            from extractors.location_extractor import LocationExtractor as RealExtractor
            extractor = RealExtractor()
            extracted = extractor.extract(text)
            
            if extracted:
                for location in extracted:
                    locations.append({
                        'name': location.get('name', location.get('value', '')),
                        'location_type': location.get('type', 'GENERAL'),
                        'country': location.get('country', ''),
                        'city': location.get('city', ''),
                        'coordinates': location.get('coordinates')
                    })
                return locations
        except ImportError:
            pass
        
        # US State abbreviations
        state_abbr = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
        }
        
        # Pattern: City, ST (e.g., "San Francisco, CA")
        city_state_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})\b'
        for match in re.finditer(city_state_pattern, text):
            city = match.group(1)
            state = match.group(2)
            if state in state_abbr:
                locations.append({
                    'name': f"{city}, {state}",
                    'location_type': 'CITY',
                    'city': city,
                    'state': state,
                    'country': 'USA'
                })
        
        # Pattern: Full state name (e.g., "California")
        full_states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
                       'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
                       'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
                       'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
                       'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
                       'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
                       'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
                       'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
                       'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
                       'West Virginia', 'Wisconsin', 'Wyoming']
        
        for state in full_states:
            pattern = rf'\b{state}\b'
            if re.search(pattern, text):
                locations.append({
                    'name': state,
                    'location_type': 'STATE',
                    'state': state,
                    'country': 'USA'
                })
        
        # Country names
        countries = ['United States', 'USA', 'Canada', 'Mexico', 'France', 'Germany',
                     'United Kingdom', 'UK', 'Japan', 'China', 'India', 'Brazil', 'Australia',
                     'Spain', 'Italy', 'Netherlands', 'Sweden', 'Norway', 'Denmark']
        
        for country in countries:
            pattern = rf'\b{country}\b'
            if re.search(pattern, text):
                locations.append({
                    'name': country,
                    'location_type': 'COUNTRY',
                    'country': country
                })
        
        # Street addresses
        address_pattern = r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b'
        for match in re.finditer(address_pattern, text):
            locations.append({
                'name': match.group(),
                'location_type': 'ADDRESS'
            })
        
        # ZIP codes
        zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
        for match in re.finditer(zip_pattern, text):
            locations.append({
                'name': match.group(),
                'location_type': 'ZIPCODE',
                'postal_code': match.group()
            })
        
        return locations
    
    def _save_locations(self, document_id: int, locations: list) -> int:
        """
        Save locations to the database.
        
        Args:
            document_id: Document ID
            locations: List of location dicts
            
        Returns:
            Number of locations saved
        """
        if not locations:
            return 0
        
        saved_count = 0
        
        for location in locations:
            name = location.get('name', '')
            location_type = location.get('location_type', 'GENERAL')
            
            # Save location
            location_id = self.backend.save_location(
                name=name,
                location_type=location_type,
                address=location.get('address', ''),
                city=location.get('city', ''),
                state=location.get('state', ''),
                country=location.get('country', ''),
                postal_code=location.get('postal_code', ''),
                coordinates=location.get('coordinates')
            )
            
            if location_id:
                # Link location to document
                self.backend.add_location_to_document(document_id, location_id)
                saved_count += 1
        
        return saved_count