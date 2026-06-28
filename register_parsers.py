from parser_registry import ParserRegistry
from json_parser import JsonParser
from yaml_parser import YamlParser
from csv_parser import CsvParser
from ini_parser import IniParser
from toml_parser import TomlParser
from xml_parser import XmlParser
from python_parser import PythonParser

registry = ParserRegistry()
registry.register('.json', JsonParser())
registry.register('.yaml', YamlParser())
registry.register('.csv', CsvParser())
registry.register('.ini', IniParser())
registry.register('.toml', TomlParser())
registry.register('.xml', XmlParser())
registry.register('.py', PythonParser())
