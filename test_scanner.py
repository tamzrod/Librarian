import os
from scanner import parse_file
from register_parsers import registry


def test_scanner():
    sample_files = [f for f in os.listdir('.') if f.startswith('sample.') and os.path.isfile(f)]
    
    for filename in sample_files:
        extension = os.path.splitext(filename)[1].lower()
        parser = registry.get_parser(extension)
        parser_name = parser.__class__.__name__ if parser else None
        
        result = parse_file(filename)
        
        print(f"Filename: {filename}")
        print(f"  Extension: {extension}")
        print(f"  Parser selected: {parser_name}")
        print(f"  Character count: {result['character_count'] if result else None}")
        print(f"  Structured data exists: {result['structured_data'] is not None if result else False}")
        print()


if __name__ == "__main__":
    test_scanner()
