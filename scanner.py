import os
import hashlib
from datetime import datetime
import json
from register_parsers import registry

def parse_file(file_path):
    extension = os.path.splitext(file_path)[1].lower()
    parser = registry.get_parser(extension)
    if parser is None:
        return None
    return parser.parse(file_path)

def get_file_metadata(file_path):
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return {
            'path': file_path,
            'filename': os.path.basename(file_path),
            'extension': os.path.splitext(file_path)[1],
            'size': os.path.getsize(file_path),
            'modified_timestamp': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            'mime_type': None,  # Placeholder for MIME type
            'sha256_hash': file_hash
        }
    except Exception as e:
        return None

def get_directory_metadata(dir_path):
    return {
        'path': dir_path,
        'type': 'directory'
    }

def scan_directory(root_dir):
    files_scanned = 0
    dirs_scanned = 0
    errors_encountered = 0
    inventory = []

    for root, dirs, files in os.walk(root_dir):
        if any(exclude in root for exclude in ['.git', '__pycache__', '.venv', 'node_modules']):
            continue

        for dir_name in dirs:
            full_path = os.path.join(root, dir_name)
            inventory.append(get_directory_metadata(full_path))
            dirs_scanned += 1

        for file_name in files:
            full_path = os.path.join(root, file_name)
            metadata = get_file_metadata(full_path)
            if metadata:
                inventory.append(metadata)
                files_scanned += 1
            else:
                errors_encountered += 1

    print(f'Files scanned: {files_scanned}')
    print(f'Directories scanned: {dirs_scanned}')
    print(f'Errors encountered: {errors_encountered}')
    return inventory

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('Usage: python scanner.py <directory_path>')
        sys.exit(1)
    
    directory_to_scan = sys.argv[1]
    scan_results = scan_directory(directory_to_scan)
    with open('scan_results.json', 'w') as f:
        json.dump(scan_results, f)


