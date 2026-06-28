import yaml


class YamlParser:
    def parse(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                original_text = file.read()

            structured_data = yaml.safe_load(original_text)

            return {
                "text": original_text,
                "structured_data": structured_data,
                "character_count": len(original_text),
                "extension": ".yaml"
            }

        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None
