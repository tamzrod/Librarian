from registry.parser_registry import ParserRegistry
from parsers.json_parser import JsonParser
from parsers.yaml_parser import YamlParser
from parsers.csv_parser import CsvParser
from parsers.ini_parser import IniParser
from parsers.toml_parser import TomlParser
from parsers.xml_parser import XmlParser
from parsers.python_parser import PythonParser
from parsers.text_parser import TextParser
from parsers.image_parser import ImageParser

registry = ParserRegistry()
registry.register('.json', JsonParser())
registry.register('.yaml', YamlParser())
registry.register('.csv', CsvParser())
registry.register('.ini', IniParser())
registry.register('.toml', TomlParser())
registry.register('.xml', XmlParser())
registry.register('.py', PythonParser())
registry.register('.txt', TextParser())
registry.register('.md', TextParser())

# Image parser - Artifact Ingestion Phase 1
# Required formats
registry.register('.jpg', ImageParser())
registry.register('.jpeg', ImageParser())
registry.register('.png', ImageParser())
registry.register('.heic', ImageParser())
registry.register('.webp', ImageParser())

# Optional formats
registry.register('.bmp', ImageParser())
registry.register('.tiff', ImageParser())
registry.register('.tif', ImageParser())
registry.register('.gif', ImageParser())
