from parsers.csv_parser import CsvParser
from parsers.ini_parser import IniParser
from parsers.json_parser import JsonParser
from parsers.toml_parser import TomlParser
from parsers.xml_parser import XmlParser
from parsers.yaml_parser import YamlParser
from parsers.image_parser import ImageParser


SAMPLE_DIR = "samples/structured"
SAMPLES_DIR = "samples"


def test_parser(parser, sample_file):
    result = parser.parse(sample_file)
    if result:
        print(f"Parser: {parser.__class__.__name__}")
        print(f"  Extension: {result['extension']}")
        print(f"  Character count: {result['character_count']}")
        print(f"  Structured data present: {result['structured_data'] is not None}")
        print()


def test_image_parser():
    """Test the ImageParser for artifact ingestion."""
    parser = ImageParser()
    
    # Test with sample images
    test_images = [
        f"{SAMPLES_DIR}/IMG_20260101_122510.jpg",
        f"{SAMPLES_DIR}/IMG_20260108_072710.jpg",
        f"{SAMPLES_DIR}/730749825_27677388005230048_9025611458864199539_n.jpeg",
    ]
    
    print("=" * 70)
    print("IMAGE PARSER TEST - Artifact Ingestion Phase 1")
    print("=" * 70)
    print()
    
    for image_path in test_images:
        print(f"Testing: {image_path}")
        result = parser.parse(image_path)
        
        if result:
            print(f"  ✓ Parser: {result['parser']}")
            print(f"  ✓ Extension: {result['extension']}")
            print(f"  ✓ MIME type: {result['structured_data']['mime_type']}")
            print(f"  ✓ Dimensions: {result['structured_data']['width']}x{result['structured_data']['height']}")
            print(f"  ✓ File size: {result['character_count']:,} bytes")
            if result['structured_data']['aspect_ratio']:
                print(f"  ✓ Aspect ratio: {result['structured_data']['aspect_ratio']}")
            print()
        else:
            print(f"  ✗ Failed to parse image")
            print()
    
    print("=" * 70)
    print("IMAGE PARSER TEST COMPLETE")
    print("=" * 70)
    print()


if __name__ == "__main__":
    test_parser(CsvParser(), f"{SAMPLE_DIR}/sample.csv")
    test_parser(IniParser(), f"{SAMPLE_DIR}/sample.ini")
    test_parser(JsonParser(), f"{SAMPLE_DIR}/sample.json")
    test_parser(TomlParser(), f"{SAMPLE_DIR}/sample.toml")
    test_parser(XmlParser(), f"{SAMPLE_DIR}/sample.xml")
    test_parser(YamlParser(), f"{SAMPLE_DIR}/sample.yaml")
    test_image_parser()
