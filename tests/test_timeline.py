import json
from core.timeline_builder import build_timeline

# Create a sample index with documents that have timestamps
sample_index = [
    {
        'path': 'samples/IMG_20260101_122510.jpg',
        'text': 'Test image from January 1st',
        'structured_data': {
            'timestamp': '2026:01:01 12:25:10',
            'camera_make': 'HONOR',
            'camera_model': 'BRP-NX1',
            'gps_latitude': 14.635189,
            'gps_longitude': 121.092548
        },
        'modified_time': None,
        'entities': []
    },
    {
        'path': 'samples/IMG_20260108_072710.jpg',
        'text': 'Test image from January 8th',
        'structured_data': {
            'timestamp': '2026:01:08 07:27:10',
            'camera_make': 'HONOR',
            'camera_model': 'BRP-NX1'
        },
        'modified_time': None,
        'entities': [
            {'type': 'location', 'value': 'Manila', 'source': 'samples/IMG_20260108_072710.jpg'}
        ]
    },
    {
        'path': 'samples/documents/meeting_notes.md',
        'text': 'Meeting notes from March 2025',
        'structured_data': None,
        'modified_time': '2025-03-12',
        'entities': []
    },
    {
        'path': 'samples/documents/report.txt',
        'text': 'Report file without timestamp',
        'structured_data': None,
        'modified_time': None,
        'entities': []
    }
]

timeline = build_timeline(sample_index)

for item in timeline:
    print(json.dumps(item, indent=2))