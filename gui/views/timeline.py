"""
Timeline View

Displays events in chronological order with filtering.
"""

from gui.widgets.timeline_widget import (
    create_timeline_widget,
    update_timeline,
    show_loading,
    get_filters
)


def create_timeline_view(parent, api_client):
    """Create timeline view with event list and filters."""
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
    from PySide6.QtCore import QThread, Signal
    
    class TimelineWorker(QThread):
        """Worker thread for loading timeline without blocking UI."""
        finished = Signal(dict)
        error = Signal(str)
        
        def __init__(self, api_client, filters):
            super().__init__()
            self.api_client = api_client
            self.filters = filters
        
        def run(self):
            try:
                data = self.api_client.get_timeline(**self.filters)
                self.finished.emit(data)
            except Exception as e:
                self.error.emit(str(e))
    
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    
    # Timeline widget
    timeline_widget = create_timeline_widget(widget, api_client)
    layout.addWidget(timeline_widget)
    
    # Store references
    widget.timeline_widget = timeline_widget
    widget.api_client = api_client
    widget.current_worker = None
    
    # Connect signals
    def on_refresh():
        # Disable refresh button
        widget.timeline_widget.refresh_button.setEnabled(False)
        
        # Show loading
        show_loading(widget.timeline_widget, "Loading timeline...")
        
        # Get filters
        filters = get_filters(widget.timeline_widget)
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Start worker thread
        widget.current_worker = TimelineWorker(api_client, filters)
        
        def on_finished(data):
            update_timeline(widget.timeline_widget, data)
            widget.timeline_widget.refresh_button.setEnabled(True)
            widget.current_worker = None
        
        def on_error(error_msg):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(f"Failed to load timeline:\n{error_msg}")
            msg.exec()
            widget.timeline_widget.refresh_button.setEnabled(True)
            widget.current_worker = None
        
        widget.current_worker.finished.connect(on_finished)
        widget.current_worker.error.connect(on_error)
        widget.current_worker.start()
    
    widget.timeline_widget.refresh_button.clicked.connect(on_refresh)
    
    # Load initial data
    on_refresh()
    
    return widget
