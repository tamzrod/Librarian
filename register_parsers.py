from parser_registry import ParserRegistry
registry = ParserRegistry()
registry.register('.txt', 'PlainTextParser')
registry.register('.md', 'PlainTextParser')
