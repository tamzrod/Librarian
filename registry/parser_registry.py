from pathlib import Path


class ParserRegistry:
    def __init__(self):
        self.parsers = {}

    def register(self, extension, parser):
        self.parsers[extension] = parser

    def get_parser(self, file_path):
        """Get parser for a file path or extension."""
        if isinstance(file_path, Path):
            file_path = str(file_path)
        if isinstance(file_path, str):
            # Extract extension and try both with and without dot
            ext = Path(file_path).suffix.lower()
            if ext in self.parsers:
                return self.parsers[ext]
            # Also try without dot
            if ext.startswith('.') and ext[1:] in self.parsers:
                return self.parsers[ext[1:]]
        return self.parsers.get(file_path, None)
