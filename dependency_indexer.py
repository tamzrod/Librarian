import re


def extract_dependencies(file_path, text):
    imports = []
    seen = set()
    
    import_pattern = re.compile(r'^import\s+(\S+)', re.MULTILINE)
    from_import_pattern = re.compile(r'^from\s+(\S+)\s+import', re.MULTILINE)
    
    for match in import_pattern.finditer(text):
        module = match.group(1)
        if module not in seen:
            imports.append(module)
            seen.add(module)
    
    for match in from_import_pattern.finditer(text):
        module = match.group(1)
        if module not in seen:
            imports.append(module)
            seen.add(module)
    
    return {
        "file": file_path,
        "imports": imports
    }
