import xml.etree.ElementTree as ET


class XmlParser:
    def parse(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                original_text = file.read()

            structured_data = ET.parse(file_path).getroot()
            structured_data = self._element_to_dict(structured_data)

            return {
                "text": original_text,
                "structured_data": structured_data,
                "character_count": len(original_text),
                "extension": ".xml"
            }

        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None

    def _element_to_dict(self, element):
        result = {}
        if element.attrib:
            result["@attributes"] = element.attrib
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result["#text"] = element.text.strip()
        for child in element:
            child_dict = self._element_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
        return result
