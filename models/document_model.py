class Document:
    def __init__(self, path, extension, text, structured_data, character_count, chunks=None):
        self.path = path
        self.extension = extension
        self.text = text
        self.structured_data = structured_data
        self.character_count = character_count
        self.chunks = chunks if chunks is not None else []

    def to_dict(self):
        return {
            'path': self.path,
            'extension': self.extension,
            'text': self.text,
            'structured_data': self.structured_data,
            'character_count': self.character_count,
            'chunks': self.chunks
        }
