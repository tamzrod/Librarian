import csv


class CsvParser:
    def parse(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                original_text = file.read()

            with open(file_path, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                structured_data = list(reader)

            return {
                "text": original_text,
                "structured_data": structured_data,
                "character_count": len(original_text),
                "extension": ".csv"
            }

        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None
