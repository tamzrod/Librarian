import configparser


class IniParser:
    def parse(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                original_text = file.read()

            config = configparser.ConfigParser()
            config.read_string(original_text)

            structured_data = {section: dict(config[section]) for section in config.sections()}

            return {
                "text": original_text,
                "structured_data": structured_data,
                "character_count": len(original_text),
                "extension": ".ini"
            }

        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None
