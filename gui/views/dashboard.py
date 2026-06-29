"""
Dashboard View

Displays library statistics from API.
"""

from gui.widgets.stats_widget import create_stats_widget, update_stats


def create_dashboard_view(parent, api_client):
    """Create dashboard view with stats and refresh button."""
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox
    from PySide6.QtCore import Qt
    
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    
    # Header with refresh button
    header_layout = QVBoxLayout()
    
    refresh_button = QPushButton("Refresh Statistics")
    refresh_button.setFixedSize(150, 35)
    refresh_button.setStyleSheet("""
        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #106ebe;
        }
    """)
    
    layout.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignRight)
    
    # Stats widget
    stats_widget = create_stats_widget(widget, api_client)
    layout.addWidget(stats_widget)
    
    # Store references
    widget.refresh_button = refresh_button
    widget.stats_widget = stats_widget
    
    return widget


def load_stats(widget, api_client):
    """Load stats from API and update widget."""
    from PySide6.QtWidgets import QMessageBox
    try:
        stats = api_client.get_stats()
        update_stats(widget.stats_widget, stats)
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(f"Failed to load statistics:\n{str(e)}")
        msg.exec()
