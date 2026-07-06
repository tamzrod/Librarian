# Librarian Test Image Samples

This folder contains a small set of public domain/CC0 images for validating Librarian plugins.

## Purpose

These images are used for:
- Object Detection plugin validation (YOLOv8n)
- EXIF metadata extraction validation
- Photo trace/timeline validation
- Plugin interactions validation

## Source

New images are sourced from [Unsplash](https://unsplash.com/) under the [Creative Commons Zero (CC0)](https://creativecommons.org/publicdomain/zero/1.0/) license, prior to their license change in June 2017.

Existing images (IMG_*.jpg) are sample photos with typical mobile EXIF metadata.

## Image Catalog

### Primary Test Images (Unsplash CC0)

| Filename | Description | Expected Objects | Categories |
|----------|-------------|------------------|------------|
| `bicycle_street.jpg` | Bicycle parked on street | bicycle, car | outdoor, multi-object |
| `building_modern.jpg` | Modern architecture | building | outdoor, gps |
| `car_urban.jpg` | Car in urban setting | car, person | outdoor, gps, multi-object |
| `cat_indoor.jpg` | Indoor cat photo | cat | indoor |
| `dog_outdoor.jpg` | Dog outdoors | dog | outdoor |
| `highway.jpg` | Highway scene | car, road, sky | outdoor, gps |
| `living_room.jpg` | Living room interior | furniture, sofa, chair | indoor, no-gps |
| `multi_object_street.jpg` | Street with multiple objects | car, person, building | outdoor, multi-object |
| `office_meeting.jpg` | Meeting room | table, chair, person | indoor, no-gps |
| `person_portrait.jpg` | Person portrait | person | outdoor, gps |
| `sky_landscape.jpg` | Landscape with sky | sky, landscape, hill | outdoor |
| `street_scene.jpg` | City street scene | building, car, person | outdoor, gps, multi-object |

### Existing Sample Images

| Filename | Description | Expected Objects | Categories |
|----------|-------------|------------------|------------|
| `IMG_20260101_122510.jpg` | Sample photo | varies | gps, outdoor |
| `IMG_20260108_072710.jpg` | Sample photo | varies | gps, outdoor |

### Directory Organization

```
samples/images/
├── gps/           # Images with GPS coordinates (expected)
├── no-gps/        # Images without GPS coordinates
├── multi-object/  # Images with multiple detectable objects
├── indoor/        # Indoor scene images
└── outdoor/       # Outdoor scene images
```

**Note:** Many images appear in multiple categories for flexibility.

## Validation Checklist

### Object Detection (YOLOv8n)

- [ ] `bicycle_street.jpg` - Detects bicycle
- [ ] `car_urban.jpg` - Detects car
- [ ] `cat_indoor.jpg` - Detects cat
- [ ] `dog_outdoor.jpg` - Detects dog
- [ ] `multi_object_street.jpg` - Detects multiple objects
- [ ] `person_portrait.jpg` - Detects person
- [ ] `street_scene.jpg` - Detects multiple objects (car, person, building)
- [ ] `sky_landscape.jpg` - Minimal objects (sky/landscape)
- [ ] `living_room.jpg` - Detects furniture

### EXIF Metadata

- [ ] GPS extraction from tagged images
- [ ] Camera make/model extraction
- [ ] Date/time extraction
- [ ] Orientation detection (portrait vs landscape)

### Photo Trace

- [ ] Timeline generation
- [ ] Map marker generation (for GPS images)
- [ ] Camera filtering

## Non-Goals

This is NOT:
- A benchmark dataset
- Training data
- A commercial collection
- An exhaustive test suite

## Adding Images

To add new test images:

1. Download from a CC0/public domain source
2. Verify image loads correctly
3. Add entry to this README with:
   - Filename
   - Source URL
   - Expected objects
   - Expected metadata
   - Validation purpose

## Image Sources

- [Unsplash](https://unsplash.com/) - CC0 images (pre-June 2017 uploads)
- [Wikimedia Commons](https://commons.wikimedia.org/) - Public domain and CC0 images
- [PxHere](https://pxhere.com/) - CC0 images
- [Rawpixel](https://www.rawpixel.com/) - Public domain images
