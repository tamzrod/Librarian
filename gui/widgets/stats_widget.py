"""
Stats Widget for Dashboard View

Displays library statistics from API.
"""


def create_stats_widget(parent, api_client):
    """Create stats widget with grid layout showing library statistics."""
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame
    from PySide6.QtCore import Qt
    
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    
    # Title
    title = QLabel("Library Statistics")
    title.setStyleSheet("font-size: 18px; font-weight: bold;")
    layout.addWidget(title)
    
    # Stats grid
    grid = QGridLayout()
    grid.setSpacing(10)
    
    # Create stat labels
    stats_data = {
        "Library Root": api_client.base_url,
        "Documents": "Loading...",
        "Entities": "Loading...",
        "Events": "Loading...",
        "Locations": "Loading...",
        "Parsers": "Loading...",
        "Watcher": "Loading...",
        "Last Scan": "Loading..."
    }
    
    row = 0
    col = 0
    labels = {}
    
    for key, value in stats_data.items():
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        frame.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        frame_layout = QVBoxLayout(frame)
        
        key_label = QLabel(key)
        key_label.setStyleSheet("font-size: 12px; color: #666;")
        key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(key_label)
        
        value_label = QLabel(str(value))
        value_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setWordWrap(True)
        frame_layout.addWidget(value_label)
        
        grid.addWidget(frame, row, col)
        labels[key] = value_label
        
        col += 1
        if col > 1:
            col = 0
            row += 1
    
    layout.addLayout(grid)
    layout.addStretch()
    
    # Store reference to update later
    widget.stats_labels = labels
    
    return widget


def update_stats(widget, stats: dict):
    """Update stats widget with new data."""
    labels = widget.stats_labels
    
    if "library_root" in stats:
        labels["Library Root"].setText(stats["library_root"])
    
    docs = stats.get("documents", {})
    labels["Documents"].setText(f"{docs.get('total', 0)}")
    
    entities = stats.get("entities", {})
    labels["Entities"].setText(f"{entities.get('total', 0)}")
    
    events = stats.get("events", {})
    labels["Events"].setText(f"{events.get('total', 0)}")
    
    locations = stats.get("locations", {})
    labels["Locations"].setText(f"{locations.get('total', 0)}")
    
    parsers = stats.get("parsers", {})
    labels["Parsers"].setText(f"{parsers.get('count', 0)}")
    
    watcher = stats.get("watcher", {})
    active = watcher.get("active", False)
    labels["Watcher"].setText("Active" if active else "Inactive")
    labels["Watcher"].setStyleSheet(
        "font-size: 16px; font-weight: bold; color: #0a0; " if active 
        else "font-size: 16px; font-weight: bold; color: #666; "
    )
    
    last_scan = watcher.get("last_scan") or "Never"
    labels["Last Scan"].setText(last_scan[:19] if last_scan != "Never" else last_scan)
