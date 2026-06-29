"""
Timeline Widget for Timeline View

Displays events in chronological order with filtering.
"""


def create_timeline_widget(parent, api_client):
    """Create timeline display widget with filters."""
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QPushButton, QTableWidget, QTableWidgetItem,
        QHeaderView, QFrame, QLineEdit, QComboBox
    )
    from PySide6.QtCore import Qt, QSize
    
    widget = QWidget(parent)
    main_layout = QVBoxLayout(widget)
    
    # Filters section
    filter_frame = QFrame()
    filter_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    filter_layout = QGridLayout(filter_frame)
    
    # Start date
    filter_layout.addWidget(QLabel("Start Date:"), 0, 0)
    start_input = QLineEdit()
    start_input.setPlaceholderText("YYYY-MM-DD")
    start_input.setMaximumWidth(120)
    filter_layout.addWidget(start_input, 0, 1)
    
    # End date
    filter_layout.addWidget(QLabel("End Date:"), 0, 2)
    end_input = QLineEdit()
    end_input.setPlaceholderText("YYYY-MM-DD")
    end_input.setMaximumWidth(120)
    filter_layout.addWidget(end_input, 0, 3)
    
    # Entity filter
    filter_layout.addWidget(QLabel("Entity:"), 0, 4)
    entity_input = QLineEdit()
    entity_input.setPlaceholderText("Filter by entity...")
    filter_layout.addWidget(entity_input, 0, 5)
    
    # Event type
    filter_layout.addWidget(QLabel("Event Type:"), 1, 0)
    event_type_combo = QComboBox()
    event_type_combo.addItems(["All", "site_visit", "photo", "signature", "meeting", "purchase"])
    filter_layout.addWidget(event_type_combo, 1, 1)
    
    # Refresh button
    refresh_button = QPushButton("Refresh")
    refresh_button.setFixedSize(QSize(100, 30))
    refresh_button.setStyleSheet("""
        QPushButton {
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #218838;
        }
    """)
    filter_layout.addWidget(refresh_button, 1, 5, 1, 1, Qt.AlignmentFlag.AlignRight)
    
    main_layout.addWidget(filter_frame)
    
    # Results count
    results_label = QLabel("No events loaded")
    results_label.setStyleSheet("font-size: 12px; color: #666; padding: 5px 0;")
    main_layout.addWidget(results_label)
    
    # Timeline table
    table = QTableWidget()
    table.setColumnCount(4)
    table.setHorizontalHeaderLabels(["Timestamp", "Event Type", "Description", "Location"])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
    table.setStyleSheet("""
        QTableWidget {
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        QTableWidget::item {
            padding: 8px;
        }
        QHeaderView::section {
            background-color: #f5f5f5;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
    """)
    main_layout.addWidget(table)
    
    # Loading indicator
    loading_label = QLabel("")
    loading_label.setStyleSheet("color: #666; font-style: italic;")
    loading_label.setVisible(False)
    main_layout.addWidget(loading_label)
    
    # Store widgets for access
    widget.start_input = start_input
    widget.end_input = end_input
    widget.entity_input = entity_input
    widget.event_type_combo = event_type_combo
    widget.refresh_button = refresh_button
    widget.results_label = results_label
    widget.table = table
    widget.loading_label = loading_label
    
    return widget


def update_timeline(widget, data: dict):
    """Update timeline table with new data."""
    events = data.get("data", [])
    pagination = data.get("pagination", {})
    filters = data.get("filters", {})
    
    widget.loading_label.setVisible(False)
    
    # Update results count
    total = pagination.get("total", len(events))
    returned = pagination.get("returned", len(events))
    widget.results_label.setText(f"Showing {returned} of {total} events")
    
    # Build filter summary
    filter_parts = []
    if filters.get("start"):
        filter_parts.append(f"Start: {filters['start']}")
    if filters.get("end"):
        filter_parts.append(f"End: {filters['end']}")
    if filters.get("entity"):
        filter_parts.append(f"Entity: {filters['entity']}")
    if filters.get("event_type"):
        filter_parts.append(f"Type: {filters['event_type']}")
    
    if filter_parts:
        widget.results_label.setText(
            f"Showing {returned} of {total} events | Filters: {' | '.join(filter_parts)}"
        )
    
    # Clear and populate table
    widget.table.setRowCount(0)
    
    if not events:
        widget.table.setRowCount(1)
        widget.table.setItem(0, 0, QTableWidgetItem("No events found"))
        widget.table.setItem(0, 1, QTableWidgetItem("-"))
        widget.table.setItem(0, 2, QTableWidgetItem("No events match your filters or library is empty"))
        widget.table.setItem(0, 3, QTableWidgetItem("-"))
        return
    
    widget.table.setRowCount(len(events))
    
    for row, event in enumerate(events):
        timestamp = event.get("timestamp", "-")[:19]  # Truncate to YYYY-MM-DDTHH:MM:SS
        event_type = event.get("event_type", "-")
        description = event.get("description", "-")
        
        # Get location from related_locations or nested structure
        location = "-"
        if "locations" in event and event["locations"]:
            location = event["locations"][0].get("name", "-")
        elif "location" in event:
            location = event["location"].get("name", "-")
        
        widget.table.setItem(row, 0, QTableWidgetItem(timestamp))
        widget.table.setItem(row, 1, QTableWidgetItem(event_type))
        widget.table.setItem(row, 2, QTableWidgetItem(description))
        widget.table.setItem(row, 3, QTableWidgetItem(location))


def show_loading(widget, message: str = "Loading..."):
    """Show loading indicator."""
    widget.loading_label.setText(message)
    widget.loading_label.setVisible(True)
    widget.table.setRowCount(0)
    widget.results_label.setText("")


def get_filters(widget) -> dict:
    """Get current filter values."""
    return {
        "start": widget.start_input.text() or None,
        "end": widget.end_input.text() or None,
        "entity": widget.entity_input.text() or None,
        "event_type": widget.event_type_combo.currentText() if widget.event_type_combo.currentText() != "All" else None
    }
