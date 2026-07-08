# Librarian GUI

A lightweight desktop GUI client for Librarian that communicates **exclusively** via the REST API.

## Architecture

The GUI is a completely separate client application. It **never imports**:
- `core/*`
- `storage/*`
- `parsers/*`
- `extractors/*`
- `postgres_backend.py`

The REST API is the **only integration point**.

## Requirements

- Python 3.9+
- PySide6 (preferred) or tkinter (built-in fallback)
- requests library
- Running Librarian API server

## Installation

```bash
cd gui
pip install -r requirements.txt
```

## Configuration

Set the API URL via environment variable:

```bash
export LIBRARIAN_API_URL=http://localhost:8001
```

Deprecated alias: `API_URL`. If neither variable is set, the GUI defaults to `http://localhost:8001`.

## Running

```bash
python main.py
```

## Features

### Dashboard View
- Library root path display
- Document count
- Entity count
- Event count
- Location count
- Parser count
- Watcher status
- Last scan timestamp

### Ask View
- Natural language question input
- Answer display with confidence score
- Evidence summary
- Trace details (expandable)

### Timeline View
- Chronological event list
- Filters: start date, end date, entity, event type
- Refresh functionality

## Navigation

Three tabs only:
1. **Dashboard** - Library statistics
2. **Ask** - Question answering
3. **Timeline** - Event timeline

No settings page. No collection management. No folder picker. No database configuration.

The library root comes from the server.

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/stats` | GET | Load statistics |
| `/api/v1/questions` | POST | Ask a question |
| `/api/v1/questions/{id}` | GET | Get question history |
| `/api/v1/timeline` | GET | Get event timeline |

## Development

### Project Structure

```
gui/
├── README.md
├── requirements.txt
├── main.py              # Application entry point
├── api_client.py         # Centralized API client
├── views/
│   ├── __init__.py
│   ├── dashboard.py     # Dashboard view
│   ├── ask.py           # Ask view
│   └── timeline.py       # Timeline view
├── widgets/
│   ├── __init__.py
│   ├── stats_widget.py      # Statistics display
│   ├── question_widget.py   # Question input/output
│   └── timeline_widget.py   # Timeline table
└── assets/
    └── .gitkeep
```

### Adding New Views

1. Create a new view file in `views/`
2. Create corresponding widgets in `widgets/`
3. Register the view in `main.py`
4. All API calls must go through `api_client.py`
