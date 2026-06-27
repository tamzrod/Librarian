import json

class JsonParser:
    def parse(self, file_path):
        try:
            with open(file_path, 'r') as file:
                original_text = file.read()
                structured_data = json.loads(original_text)
                character_count = len(original_text)
                return {
                    "text": original_text,
                    "structured_data": structured_data,
                    "character_count": character_count,
                    "extension": ".json"
                }
        except (json.JSONDecodeError, FileNotFoundError):
            return None


