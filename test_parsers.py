from csv_parser import CsvParser
from ini_parser import IniParser
from json_parser import JsonParser
from toml_parser import TomlParser
from xml_parser import XmlParser
from yaml_parser import YamlParser


SAMPLE_DIR = "samples/structured"


def test_parser(parser, sample_file):
    result = parser.parse(sample_file)
    if result:
        print(f"Parser: {parser.__class__.__name__}")
        print(f"  Extension: {result['extension']}")
        print(f"  Character count: {result['character_count']}")
        print(f"  Structured data present: {result['structured_data'] is not None}")
        print()


if __name__ == "__main__":
    test_parser(CsvParser(), f"{SAMPLE_DIR}/sample.csv")
    test_parser(IniParser(), f"{SAMPLE_DIR}/sample.ini")
    test_parser(JsonParser(), f"{SAMPLE_DIR}/sample.json")
    test_parser(TomlParser(), f"{SAMPLE_DIR}/sample.toml")
    test_parser(XmlParser(), f"{SAMPLE_DIR}/sample.xml")
    test_parser(YamlParser(), f"{SAMPLE_DIR}/sample.yaml")
