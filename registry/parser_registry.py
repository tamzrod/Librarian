class ParserRegistry:
    def __init__(self):
        self.parsers = {}

    def register(self, extension, parser):
        self.parsers[extension] = parser

    def get_parser(self, extension):
        return self.parsers.get(extension, None)
