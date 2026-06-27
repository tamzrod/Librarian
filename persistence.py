import json

def save_snapshot(scan_results, filename):
    try:
        with open(filename, 'w') as f:
            json.dump(scan_results, f)
    except Exception as e:
        print(f'Error saving snapshot: {e}')

def load_snapshot(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print('Snapshot file not found.')
        return []
    except json.JSONDecodeError:
        print('Error decoding JSON from snapshot file.')
        return []
    except Exception as e:
        print(f'Error loading snapshot: {e}')
        return []


