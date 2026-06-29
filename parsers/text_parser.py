class TextParser:
    """Parser for plain text files (.txt, .md, etc.)."""
    
    def parse(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return {
                "text": text,
                "structured_data": {
                    "line_count": len(text.splitlines()),
                    "word_count": len(text.split())
                },
                "character_count": len(text),
                "extension": ".txt"
            }
        except Exception:
            return None
