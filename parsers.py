from abc import ABC, abstractmethod
import os

class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path):
        pass

class PlainTextParser(DocumentParser):
    def parse(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                character_count = len(text)
                word_count = len(text.split())
                line_count = len(text.splitlines())
                extension = os.path.splitext(file_path)[1]
                return {
                    "text": text,
                    "character_count": character_count,
                    "word_count": word_count,
                    "line_count": line_count,
                    "extension": extension
                }
        except Exception as e:
            print(f'Error parsing file {file_path}: {e}')
            return None


