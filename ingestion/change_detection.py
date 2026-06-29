def compare_scans(previous_scan, current_scan):
    new = []
    modified = []
    deleted = []
    moved = []
    unchanged = []

    # Create a dictionary for previous scan with sha256 as key
    prev_dict = {item['sha256_hash']: item for item in previous_scan if 'sha256_hash' in item}
    # Create a dictionary for current scan with sha256 as key
    curr_dict = {item['sha256_hash']: item for item in current_scan if 'sha256_hash' in item}

    # Identify unchanged and moved files
    for sha, prev_item in prev_dict.items():
        if sha in curr_dict:
            curr_item = curr_dict[sha]
            if prev_item['path'] == curr_item['path']:
                unchanged.append(prev_item)
            else:
                moved.append({'from': prev_item['path'], 'to': curr_item['path']})

    # Identify modified files
    for sha, prev_item in prev_dict.items():
        if sha in curr_dict:
            curr_item = curr_dict[sha]
            if prev_item['path'] == curr_item['path'] and prev_item != curr_item:
                modified.append(prev_item)

    # Identify deleted files
    for sha, prev_item in prev_dict.items():
        if sha not in curr_dict:
            deleted.append(prev_item)

    # Identify new files
    for sha, curr_item in curr_dict.items():
        if sha not in prev_dict:
            new.append(curr_item)

    return {
        'new': new,
        'modified': modified,
        'deleted': deleted,
        'moved': moved,
        'unchanged': unchanged
    }

# Test dataset
previous_scan = [
    {'path': '/path/to/unchanged.txt', 'sha256_hash': 'hash1'},
    {'path': '/path/to/deleted.txt', 'sha256_hash': 'hash2'},
    {'path': '/path/to/moved.txt', 'sha256_hash': 'hash3'}
]

current_scan = [
    {'path': '/path/to/unchanged.txt', 'sha256_hash': 'hash1'},
    {'path': '/path/to/new.txt', 'sha256_hash': 'hash4'},
    {'path': '/path/to/moved_new.txt', 'sha256_hash': 'hash3'}
]

# Run the comparison
results = compare_scans(previous_scan, current_scan)
print(results)


