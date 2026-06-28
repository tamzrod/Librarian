try:
    import tomllib
except ImportError:
    import tomli as tomllib


class TomlParser:
    def parse(self, file_path):
        try:
            with open(file_path, "rb") as file:
                original_text = file.read().decode("utf-8")

            with open(file_path, "rb") as file:
                structured_data = tomllib.load(file)

            return {
                "text": original_text,
                "structured_data": structured_data,
                "character_count": len(original_text),
                "extension": ".toml"
            }

        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None
