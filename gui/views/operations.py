"""
Operations Dashboard View

Read-only operator console for monitoring Librarian system health and activity.
This dashboard is designed to answer: "What is Librarian doing right now?"
"""

from typing import Optional, Callable
from datetime import datetime


def create_operations_view(parent, api_client) -> 'QWidget':
    """
    Create the operations dashboard view.
    
    Args:
        parent: Parent widget
        api_client: LibrarianAPIClient instance
    
    Returns:
        QWidget containing the operations dashboard
    """
    try:
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
            QLabel, QFrame, QTableWidget, QTableWidgetItem,
            QHeaderView, QScrollArea, QGroupBox, QPushButton,
            QLineEdit, QComboBox, QTextEdit, QSplitter, QTabWidget,
            QProgressBar, QListWidget, QListWidgetItem
        )
        from PySide6.QtCore import Qt, QTimer, Signal
        from PySide6.QtGui import QFont, QColor
    except ImportError:
        return _create_tkinter_operations_view(parent, api_client)
    
    class OperationsDashboard(QWidget):
        """Main operations dashboard widget."""
        
        # Signals for thread-safe updates
        overview_updated = Signal(dict)
        activity_updated = Signal(list)
        jobs_updated = Signal(list, dict)
        
        def __init__(self, api_client):
            super().__init__()
            self.api_client = api_client
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self.refresh_all)
            
            self._init_ui()
            self._connect_signals()
            
            # Initial load
            self.refresh_all()
            
            # Start auto-refresh (5 seconds for activity feed)
            self.refresh_timer.start(5000)
        
        def _init_ui(self):
            """Initialize the UI layout."""
            main_layout = QVBoxLayout(self)
            
            # Create tab widget for different sections
            self.tabs = QTabWidget()
            self.tabs.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    background: white;
                }
                QTabBar::tab {
                    padding: 8px 16px;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: white;
                    font-weight: bold;
                }
                QTabBar::tab:hover {
                    background-color: #e0e0e0;
                }
            """)
            
            # Tab 1: System Overview
            self.overview_tab = self._create_overview_tab()
            self.tabs.addTab(self.overview_tab, "System Overview")
            
            # Tab 2: Live Activity Feed
            self.activity_tab = self._create_activity_tab()
            self.tabs.addTab(self.activity_tab, "Live Activity")
            
            # Tab 3: Job Queue
            self.queue_tab = self._create_queue_tab()
            self.tabs.addTab(self.queue_tab, "Job Queue")
            
            # Tab 4: Documents
            self.documents_tab = self._create_documents_tab()
            self.tabs.addTab(self.documents_tab, "Documents")
            
            # Tab 5: Document Detail (shown when document selected)
            self.detail_tab = self._create_document_detail_tab()
            self.tabs.addTab(self.detail_tab, "Document Detail")
            
            main_layout.addWidget(self.tabs)
            
            # Status bar
            status_layout = QHBoxLayout()
            self.status_label = QLabel("Connecting...")
            self.status_label.setStyleSheet("color: gray; font-size: 11px;")
            self.last_update_label = QLabel("")
            self.last_update_label.setStyleSheet("color: gray; font-size: 11px;")
            status_layout.addWidget(self.status_label)
            status_layout.addStretch()
            status_layout.addWidget(self.last_update_label)
            main_layout.addLayout(status_layout)
        
        def _create_overview_tab(self) -> 'QWidget':
            """Create the system overview tab."""
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setSpacing(15)
            
            # Title
            title = QLabel("System Overview")
            title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
            layout.addWidget(title)
            
            # Create a grid layout for the 4 sections
            grid = QGridLayout()
            grid.setSpacing(15)
            
            # Filesystem Section
            fs_frame = self._create_section_frame("Filesystem", [
                ("Files", "files"),
                ("Documents", "documents"),
                ("Directories", "directories"),
                ("Watched Paths", "watched_paths"),
                ("Storage Used", "storage_used")
            ])
            grid.addWidget(fs_frame, 0, 0)
            
            # Knowledge Section
            kn_frame = self._create_section_frame("Knowledge", [
                ("Entities", "entities"),
                ("Relationships", "relationships"),
                ("Events", "events"),
                ("Locations", "locations"),
                ("Embeddings", "embeddings")
            ])
            grid.addWidget(kn_frame, 0, 1)
            
            # Pipeline Section
            pl_frame = self._create_section_frame("Pipeline", [
                ("Queued Jobs", "queued_jobs"),
                ("Running Jobs", "running_jobs"),
                ("Completed Jobs", "completed_jobs"),
                ("Failed Jobs", "failed_jobs"),
                ("Workers", "workers"),
                ("Oldest Job Age", "oldest_job_age")
            ])
            grid.addWidget(pl_frame, 1, 0)
            
            # System Section
            sys_frame = self._create_section_frame("System", [
                ("Database", "database_status"),
                ("Watcher", "watcher_status"),
                ("Job Processor", "job_processor_status"),
                ("API", "api_status")
            ])
            grid.addWidget(sys_frame, 1, 1)
            
            layout.addLayout(grid)
            layout.addStretch()
            
            return widget
        
        def _create_section_frame(self, title: str, fields: list) -> 'QFrame':
            """Create a section frame with labeled fields."""
            frame = QFrame()
            frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
            frame.setStyleSheet("""
                QFrame {
                    background-color: #fafafa;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 5px;
                }
            """)
            
            layout = QVBoxLayout(frame)
            layout.setSpacing(8)
            
            # Section title
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #333;
                padding: 5px;
                border-bottom: 1px solid #ddd;
                margin-bottom: 5px;
            """)
            layout.addWidget(title_label)
            
            # Create labels for each field
            for field_name, field_key in fields:
                field_layout = QHBoxLayout()
                field_layout.setSpacing(10)
                
                name_label = QLabel(f"{field_name}:")
                name_label.setStyleSheet("color: #666; min-width: 100px;")
                
                value_label = QLabel("-")
                value_label.setObjectName(f"value_{field_key}")
                value_label.setStyleSheet("font-weight: bold; color: #333;")
                
                field_layout.addWidget(name_label)
                field_layout.addWidget(value_label)
                field_layout.addStretch()
                
                layout.addLayout(field_layout)
            
            return frame
        
        def _create_activity_tab(self) -> 'QWidget':
            """Create the live activity feed tab."""
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setSpacing(10)
            
            # Header
            header_layout = QHBoxLayout()
            header = QLabel("Live Activity Feed")
            header.setStyleSheet("font-size: 16px; font-weight: bold;")
            header_layout.addWidget(header)
            
            self.activity_count_label = QLabel("(0 events)")
            self.activity_count_label.setStyleSheet("color: gray;")
            header_layout.addWidget(self.activity_count_label)
            header_layout.addStretch()
            
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(self.refresh_activity)
            header_layout.addWidget(refresh_btn)
            
            layout.addLayout(header_layout)
            
            # Activity list
            self.activity_list = QListWidget()
            self.activity_list.setStyleSheet("""
                QListWidget {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background: white;
                }
                QListWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #f0f0f0;
                }
                QListWidget::item:selected {
                    background-color: #e3f2fd;
                }
            """)
            layout.addWidget(self.activity_list)
            
            return widget
        
        def _create_queue_tab(self) -> 'QWidget':
            """Create the job queue tab."""
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setSpacing(10)
            
            # Header with filters
            header_layout = QHBoxLayout()
            header = QLabel("Job Queue")
            header.setStyleSheet("font-size: 16px; font-weight: bold;")
            header_layout.addWidget(header)
            header_layout.addStretch()
            
            # Filter controls
            self.job_filter_combo = QComboBox()
            self.job_filter_combo.addItems(["All", "QUEUED", "IN_PROGRESS", "COMPLETED", "FAILED"])
            self.job_filter_combo.currentTextChanged.connect(self.on_job_filter_changed)
            header_layout.addWidget(QLabel("Status:"))
            header_layout.addWidget(self.job_filter_combo)
            
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(self.refresh_jobs)
            header_layout.addWidget(refresh_btn)
            
            layout.addLayout(header_layout)
            
            # Job counts summary
            self.job_counts_label = QLabel("Loading...")
            self.job_counts_label.setStyleSheet("color: gray; padding: 5px;")
            layout.addWidget(self.job_counts_label)
            
            # Job table
            self.job_table = QTableWidget()
            self.job_table.setColumnCount(7)
            self.job_table.setHorizontalHeaderLabels([
                "ID", "Document", "Job Type", "Status", "Worker", "Attempts", "Age"
            ])
            self.job_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.job_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.job_table.setStyleSheet("""
                QTableWidget {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background: white;
                }
                QTableWidget::item {
                    padding: 5px;
                }
                QHeaderView::section {
                    background-color: #f5f5f5;
                    padding: 5px;
                    border: none;
                    border-bottom: 1px solid #ddd;
                    font-weight: bold;
                }
            """)
            self.job_table.itemSelectionChanged.connect(self.on_job_selected)
            layout.addWidget(self.job_table)
            
            return widget
        
        def _create_documents_tab(self) -> 'QWidget':
            """Create the documents list tab."""
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setSpacing(10)
            
            # Header
            header_layout = QHBoxLayout()
            header = QLabel("Documents")
            header.setStyleSheet("font-size: 16px; font-weight: bold;")
            header_layout.addWidget(header)
            header_layout.addStretch()
            
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(self.refresh_documents)
            header_layout.addWidget(refresh_btn)
            
            layout.addLayout(header_layout)
            
            # Documents table
            self.documents_table = QTableWidget()
            self.documents_table.setColumnCount(5)
            self.documents_table.setHorizontalHeaderLabels([
                "ID", "Path", "Status", "Size", "Parser"
            ])
            self.documents_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.documents_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.documents_table.setStyleSheet("""
                QTableWidget {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background: white;
                }
                QTableWidget::item {
                    padding: 5px;
                }
                QHeaderView::section {
                    background-color: #f5f5f5;
                    padding: 5px;
                    border: none;
                    border-bottom: 1px solid #ddd;
                    font-weight: bold;
                }
            """)
            self.documents_table.itemSelectionChanged.connect(self.on_document_selected)
            layout.addWidget(self.documents_table)
            
            return widget
        
        def _create_document_detail_tab(self) -> 'QWidget':
            """Create the document detail tab (journey + extractions)."""
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setSpacing(10)
            
            # Header
            header_layout = QHBoxLayout()
            self.detail_doc_label = QLabel("Select a document from the Documents tab")
            self.detail_doc_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            header_layout.addWidget(self.detail_doc_label)
            header_layout.addStretch()
            
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(self.refresh_document_detail)
            header_layout.addWidget(refresh_btn)
            
            layout.addLayout(header_layout)
            
            # Create inner tab widget for journey and extractions
            self.detail_tabs = QTabWidget()
            
            # Journey tab
            self.journey_widget = QWidget()
            journey_layout = QVBoxLayout(self.journey_widget)
            
            self.journey_status_label = QLabel("Status: -")
            self.journey_status_label.setStyleSheet("font-size: 14px; padding: 5px;")
            journey_layout.addWidget(self.journey_status_label)
            
            self.journey_list = QListWidget()
            self.journey_list.setStyleSheet("""
                QListWidget {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background: white;
                }
                QListWidget::item {
                    padding: 10px;
                    margin: 2px;
                    border-radius: 4px;
                }
            """)
            journey_layout.addWidget(self.journey_list)
            
            self.detail_tabs.addTab(self.journey_widget, "Journey")
            
            # Extractions tab
            self.extractions_widget = QWidget()
            extractions_layout = QVBoxLayout(self.extractions_widget)
            
            # Entities section
            entities_group = QGroupBox("Entities")
            entities_layout = QVBoxLayout(entities_group)
            self.entities_list = QListWidget()
            entities_layout.addWidget(self.entities_list)
            extractions_layout.addWidget(entities_group)
            
            # Events section
            events_group = QGroupBox("Events")
            events_layout = QVBoxLayout(events_group)
            self.events_list = QListWidget()
            events_layout.addWidget(self.events_list)
            extractions_layout.addWidget(events_group)
            
            # Locations section
            locations_group = QGroupBox("Locations")
            locations_layout = QVBoxLayout(locations_group)
            self.locations_list = QListWidget()
            locations_layout.addWidget(self.locations_list)
            extractions_layout.addWidget(locations_group)
            
            self.detail_tabs.addTab(self.extractions_widget, "Extractions")
            
            # Content preview tab
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            self.content_preview = QTextEdit()
            self.content_preview.setReadOnly(True)
            self.content_preview.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background: white;
                    font-family: monospace;
                    padding: 10px;
                }
            """)
            content_layout.addWidget(self.content_preview)
            self.detail_tabs.addTab(content_widget, "Content Preview")
            
            layout.addWidget(self.detail_tabs)
            
            return widget
        
        def _connect_signals(self):
            """Connect signals for thread-safe updates."""
            self.overview_updated.connect(self._update_overview)
            self.activity_updated.connect(self._update_activity)
            self.jobs_updated.connect(self._update_jobs)
        
        def refresh_all(self):
            """Refresh all dashboard data."""
            self.refresh_overview()
            self.refresh_activity()
            self.refresh_jobs()
            self.refresh_documents()
            
            self.last_update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        
        def refresh_overview(self):
            """Refresh the system overview."""
            try:
                data = self.api_client.get_system_overview()
                self.overview_updated.emit(data)
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                self.status_label.setStyleSheet("color: red;")
        
        def refresh_activity(self):
            """Refresh the activity feed."""
            try:
                data = self.api_client.get_activity_feed(limit=100)
                events = data.get('events', [])
                self.activity_updated.emit(events)
            except Exception as e:
                self.status_label.setText(f"Activity error: {str(e)}")
        
        def refresh_jobs(self):
            """Refresh the job queue."""
            try:
                status_filter = self.job_filter_combo.currentText()
                status = None if status_filter == "All" else status_filter
                
                data = self.api_client.get_job_queue(status=status, limit=200)
                jobs = data.get('jobs', [])
                counts = data.get('counts', {})
                self.jobs_updated.emit(jobs, counts)
            except Exception as e:
                self.status_label.setText(f"Jobs error: {str(e)}")
        
        def refresh_documents(self):
            """Refresh the documents list."""
            try:
                data = self.api_client.list_documents(limit=100)
                documents = data.get('documents', [])
                
                self.documents_table.setRowCount(len(documents))
                for i, doc in enumerate(documents):
                    self.documents_table.setItem(i, 0, QTableWidgetItem(str(doc.get('id', ''))))
                    self.documents_table.setItem(i, 1, QTableWidgetItem(doc.get('path', '')))
                    
                    status_item = QTableWidgetItem(doc.get('status', ''))
                    self._style_status_item(status_item, doc.get('status', ''))
                    self.documents_table.setItem(i, 2, status_item)
                    
                    size = doc.get('file_size')
                    size_str = f"{size:,}" if size else "-"
                    self.documents_table.setItem(i, 3, QTableWidgetItem(size_str))
                    self.documents_table.setItem(i, 4, QTableWidgetItem(doc.get('parser', '')))
            except Exception as e:
                self.status_label.setText(f"Documents error: {str(e)}")
        
        def refresh_document_detail(self):
            """Refresh the current document detail view."""
            selected = self.documents_table.selectedIndexes()
            if not selected:
                return
            
            row = selected[0].row()
            doc_id_item = self.documents_table.item(row, 0)
            if not doc_id_item:
                return
            
            try:
                doc_id = int(doc_id_item.text())
                
                # Get journey
                journey_data = self.api_client.get_document_journey(doc_id)
                self._update_journey(journey_data)
                
                # Get extractions
                extraction_data = self.api_client.get_document_extractions(doc_id)
                self._update_extractions(extraction_data)
                
            except Exception as e:
                self.status_label.setText(f"Detail error: {str(e)}")
        
        def _format_bytes(self, bytes_value: int) -> str:
            """Format bytes to human-readable string."""
            if bytes_value is None or bytes_value == 0:
                return "-"
            
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            unit_idx = 0
            value = float(bytes_value)
            
            while value >= 1024 and unit_idx < len(units) - 1:
                value /= 1024
                unit_idx += 1
            
            if unit_idx == 0:
                return f"{int(value)} {units[unit_idx]}"
            return f"{value:.1f} {units[unit_idx]}"

        def _format_duration(self, seconds: float) -> str:
            """Format seconds to human-readable duration."""
            if seconds is None or seconds == 0:
                return "-"
            
            if seconds < 60:
                return f"{int(seconds)}s"
            
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            
            if minutes < 60:
                if remaining_seconds == 0:
                    return f"{minutes}m"
                return f"{minutes}m {remaining_seconds}s"
            
            hours = minutes // 60
            remaining_minutes = minutes % 60
            
            if remaining_minutes == 0:
                return f"{hours}h"
            return f"{hours}h {remaining_minutes}m"

        def _update_overview(self, data: dict):
            """Update the overview display."""
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green;")
            
            # Field mapping: GUI label key -> API response key
            # API field names are canonical (include units)
            field_map = {
                'files': ('files', None),
                'documents': ('documents', None),
                'directories': ('directories', None),
                'watched_paths': ('watched_paths', None),
                'storage_used': ('storage_used_bytes', 'bytes'),
                'entities': ('entities', None),
                'relationships': ('relationships', None),
                'events': ('events', None),
                'locations': ('locations', None),
                'embeddings': ('embeddings', None),
                'queued_jobs': ('queued_jobs', None),
                'running_jobs': ('running_jobs', None),
                'completed_jobs': ('completed_jobs', None),
                'failed_jobs': ('failed_jobs', None),
                'workers': ('workers', None),
                'oldest_job_age': ('oldest_job_age_seconds', 'duration'),
                'database_status': ('database_status', 'status'),
                'watcher_status': ('watcher_status', 'status'),
                'job_processor_status': ('job_processor_status', 'status'),
                'api_status': ('api_status', 'status'),
            }
            
            for label_key, (api_key, format_type) in field_map.items():
                value = data.get(api_key)
                obj_name = f'value_{label_key}'
                
                if value is None:
                    value = "-"
                    display_text = "-"
                elif format_type == 'bytes':
                    display_text = self._format_bytes(value)
                elif format_type == 'duration':
                    display_text = self._format_duration(value)
                elif format_type == 'status':
                    display_text = str(value)
                elif isinstance(value, float):
                    display_text = f"{value:.1f}"
                elif isinstance(value, int):
                    display_text = f"{value:,}"
                else:
                    display_text = str(value)
                
                label = self.findChild(QLabel, obj_name)
                if label:
                    label.setText(display_text)
                    # Color status fields
                    if format_type == 'status':
                        if value in ("CONNECTED", "RUNNING", "ACTIVE", "HEALTHY"):
                            label.setStyleSheet("font-weight: bold; color: green;")
                        elif value in ("DISCONNECTED", "STOPPED"):
                            label.setStyleSheet("font-weight: bold; color: red;")
                        else:
                            label.setStyleSheet("font-weight: bold; color: orange;")
            
            # Update failed jobs in red if any
            failed_label = self.findChild(QLabel, 'value_failed_jobs')
            if failed_label and data.get('failed_jobs', 0) > 0:
                failed_label.setStyleSheet("font-weight: bold; color: red;")
        
        def _update_activity(self, events: list):
            """Update the activity feed."""
            self.activity_list.clear()
            self.activity_count_label.setText(f"({len(events)} events)")
            
            for event in events:
                timestamp = event.get('timestamp', '')[:19]  # HH:MM:SS
                message = event.get('message', '')
                level = event.get('level', 'info')
                
                item_text = f"{timestamp} {message}"
                item = QListWidgetItem(item_text)
                
                # Color by level
                if level == 'error':
                    item.setBackground(QColor('#ffebee'))
                elif level == 'warning':
                    item.setBackground(QColor('#fff8e1'))
                
                self.activity_list.addItem(item)
        
        def _update_jobs(self, jobs: list, counts: dict):
            """Update the job queue table."""
            # Update counts label
            counts_text = f"Queued: {counts.get('queued', 0)} | Running: {counts.get('in_progress', 0)} | Completed: {counts.get('completed', 0)} | Failed: {counts.get('failed', 0)}"
            self.job_counts_label.setText(counts_text)
            
            # Update table
            self.job_table.setRowCount(len(jobs))
            for i, job in enumerate(jobs):
                self.job_table.setItem(i, 0, QTableWidgetItem(str(job.get('id', ''))))
                self.job_table.setItem(i, 1, QTableWidgetItem(job.get('document_path', str(job.get('document_id', '')))))
                self.job_table.setItem(i, 2, QTableWidgetItem(job.get('job_type', '')))
                
                status_item = QTableWidgetItem(job.get('status', ''))
                self._style_status_item(status_item, job.get('status', ''))
                self.job_table.setItem(i, 3, status_item)
                
                self.job_table.setItem(i, 4, QTableWidgetItem(job.get('worker_id', '-')))
                self.job_table.setItem(i, 5, QTableWidgetItem(str(job.get('attempt_count', 0))))
                
                age = job.get('age_seconds')
                age_str = f"{age:.0f}s" if age else "-"
                self.job_table.setItem(i, 6, QTableWidgetItem(age_str))
        
        def _style_status_item(self, item: 'QTableWidgetItem', status: str):
            """Style a status table item based on status value."""
            status = status.upper()
            if status == 'COMPLETED':
                item.setBackground(QColor('#e8f5e9'))
            elif status == 'QUEUED':
                item.setBackground(QColor('#fff8e1'))
            elif status == 'IN_PROGRESS':
                item.setBackground(QColor('#e3f2fd'))
            elif status == 'FAILED' or status == 'FAILED_PERMANENT':
                item.setBackground(QColor('#ffebee'))
        
        def _update_journey(self, data: dict):
            """Update the document journey display."""
            path = data.get('path', 'Unknown')
            status = data.get('status', 'UNKNOWN')
            doc_id = data.get('document_id', 0)
            
            self.detail_doc_label.setText(f"Document {doc_id}: {path}")
            self.journey_status_label.setText(f"Status: {status}")
            
            # Get lifecycle states
            lifecycle_states = data.get('lifecycle_states', [])
            current_status = status.upper()
            
            self.journey_list.clear()
            for state in lifecycle_states:
                item = QListWidgetItem(f"○ {state}")
                
                if state == current_status:
                    item.setText(f"● {state}")
                    item.setBackground(QColor('#e3f2fd'))
                elif self._is_state_completed(state, current_status, lifecycle_states):
                    item.setText(f"✓ {state}")
                    item.setBackground(QColor('#e8f5e9'))
                
                self.journey_list.addItem(item)
            
            # Show jobs
            jobs = data.get('jobs', [])
            for job in jobs:
                job_status = job.get('status', '')
                job_type = job.get('job_type', '')
                error = job.get('error_message', '')
                
                status_icon = '●' if job_status == 'IN_PROGRESS' else ('✓' if job_status == 'COMPLETED' else '✗')
                job_text = f"{status_icon} {job_type}: {job_status}"
                if error:
                    job_text += f" - {error[:50]}..."
                
                job_item = QListWidgetItem(job_text)
                if job_status == 'COMPLETED':
                    job_item.setBackground(QColor('#e8f5e9'))
                elif job_status == 'FAILED':
                    job_item.setBackground(QColor('#ffebee'))
                
                self.journey_list.addItem(job_item)
        
        def _is_state_completed(self, state: str, current_status: str, states: list) -> bool:
            """Check if a state has been completed based on current status."""
            state_order = ['DISCOVERED', 'METADATA_INDEXED', 'CONTENT_EXTRACTED', 
                          'ENTITY_EXTRACTED', 'EVENT_EXTRACTED', 'LOCATION_EXTRACTED',
                          'RELATIONSHIPS_BUILT', 'EMBEDDED', 'COMPLETE']
            
            try:
                state_idx = state_order.index(state)
                current_idx = state_order.index(current_status) if current_status in state_order else -1
                return current_idx > state_idx
            except ValueError:
                return False
        
        def _update_extractions(self, data: dict):
            """Update the extraction results display."""
            # Entities
            self.entities_list.clear()
            entities = data.get('entities', [])
            if entities:
                for e in entities:
                    self.entities_list.addItem(f"{e.get('type', 'unknown')}: {e.get('value', '')}")
            else:
                self.entities_list.addItem("(No entities extracted)")
            
            # Events
            self.events_list.clear()
            events = data.get('events', [])
            if events:
                for e in events:
                    desc = e.get('description', '')[:50]
                    self.events_list.addItem(f"{e.get('timestamp', '')}: {e.get('type', '')} - {desc}")
            else:
                self.events_list.addItem("(No events extracted)")
            
            # Locations
            self.locations_list.clear()
            locations = data.get('locations', [])
            if locations:
                for l in locations:
                    city = l.get('city', '')
                    state = l.get('state', '')
                    country = l.get('country', '')
                    location_str = l.get('name', '')
                    if city or state or country:
                        location_str = f"{location_str} ({city}, {state}, {country})"
                    self.locations_list.addItem(location_str)
            else:
                self.locations_list.addItem("(No locations extracted)")
            
            # Content preview
            preview = data.get('content_preview', '')
            self.content_preview.setPlainText(preview or "(No content available)")
        
        def on_job_filter_changed(self, text: str):
            """Handle job filter change."""
            self.refresh_jobs()
        
        def on_job_selected(self):
            """Handle job selection."""
            selected = self.job_table.selectedIndexes()
            if selected:
                # Could show document detail for selected job
                pass
        
        def on_document_selected(self):
            """Handle document selection."""
            # Automatically switch to detail tab and load details
            self.tabs.setCurrentIndex(4)  # Document Detail tab
            self.refresh_document_detail()
        
        def close(self):
            """Clean up on close."""
            self.refresh_timer.stop()
    
    return OperationsDashboard(api_client)


def _create_tkinter_operations_view(parent, api_client) -> 'tk.Widget':
    """Create a tkinter fallback operations view."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        return None
    
    widget = tk.Frame(parent)
    
    # Title
    tk.Label(
        widget,
        text="Operations Dashboard",
        font=("Arial", 16, "bold")
    ).pack(pady=10)
    
    # Note about PySide6
    tk.Label(
        widget,
        text="For full functionality, install PySide6: pip install PySide6",
        fg="gray"
    ).pack()
    
    # System overview frame
    overview_frame = tk.LabelFrame(widget, text="System Overview", padx=10, pady=10)
    overview_frame.pack(fill='both', expand=True, padx=20, pady=10)
    
    # Stats grid
    stats_labels = {}
    for i, key in enumerate(["Database", "Watcher", "Documents", "Entities", "Jobs"]):
        row, col = divmod(i, 3)
        tk.Label(overview_frame, text=f"{key}:", anchor='w', width=15).grid(row=row, column=col*2, sticky='w')
        label = tk.Label(overview_frame, text="Loading...", anchor='w')
        label.grid(row=row, column=col*2+1, sticky='w')
        stats_labels[key] = label
    
    def refresh():
        try:
            data = api_client.get_system_overview()
            stats_labels["Database"].config(text=data.get('database_status', 'N/A'))
            stats_labels["Watcher"].config(text=data.get('watcher_status', 'N/A'))
            stats_labels["Documents"].config(text=data.get('documents', 0))
            stats_labels["Entities"].config(text=data.get('entities', 0))
            stats_labels["Jobs"].config(text=f"Q:{data.get('queued_jobs', 0)} R:{data.get('running_jobs', 0)} C:{data.get('completed_jobs', 0)}")
        except Exception as e:
            for label in stats_labels.values():
                label.config(text="Error")
    
    tk.Button(widget, text="Refresh", command=refresh).pack(pady=5)
    
    # Auto-refresh
    widget.after(5000, refresh)
    refresh()
    
    return widget
