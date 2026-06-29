import os
from ingestion.scanner import parse_file
from registry.register_parsers import registry


def test_scanner():
    sample_dir = 'samples/structured'
    sample_files = [os.path.join(sample_dir, f) for f in os.listdir(sample_dir) if f.startswith('sample.') and os.path.isfile(os.path.join(sample_dir, f))]
    
    for filepath in sample_files:
        filename = os.path.basename(filepath)
        extension = os.path.splitext(filename)[1].lower()
        parser = registry.get_parser(extension)
        parser_name = parser.__class__.__name__ if parser else None
        
        result = parse_file(filepath)
        
        print(f"Filename: {filename}")
        print(f"  Extension: {extension}")
        print(f"  Parser selected: {parser_name}")
        print(f"  Character count: {result['character_count'] if result else None}")
        print(f"  Structured data exists: {result['structured_data'] is not None if result else False}")
        print()


if __name__ == "__main__":
    test_scanner()
