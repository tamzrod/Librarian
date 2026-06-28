from librarian import Librarian


def test_librarian():
    lib = Librarian()
    lib.ingest('.')
    
    json_results = lib.search('json')
    parser_results = lib.search('parser')
    yaml_results = lib.search('yaml')
    
    scanner_deps = lib.get_dependencies('scanner.py')
    librarian_deps = lib.get_dependencies('librarian.py')
    
    print("Search results for 'json':", len(json_results))
    print("Search results for 'parser':", len(parser_results))
    print("Search results for 'yaml':", len(yaml_results))
    print()
    print("Dependencies for scanner.py:", scanner_deps)
    print("Dependencies for librarian.py:", librarian_deps)


if __name__ == "__main__":
    test_librarian()
