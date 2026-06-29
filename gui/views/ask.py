"""
Ask View

Allows user to ask questions and view answers with evidence.
"""

from gui.widgets.question_widget import (
    create_question_widget, 
    update_answer, 
    clear_answer
)


def create_ask_view(parent, api_client):
    """Create ask view with question input and answer display."""
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
    from PySide6.QtCore import QThread, Signal
    
    class AskWorker(QThread):
        """Worker thread for asking question without blocking UI."""
        finished = Signal(dict)
        error = Signal(str)
        
        def __init__(self, api_client, question):
            super().__init__()
            self.api_client = api_client
            self.question = question
        
        def run(self):
            try:
                response = self.api_client.ask_question(
                    self.question,
                    options={
                        "include_evidence": True,
                        "include_trace": True,
                        "max_evidence_items": 10
                    }
                )
                self.finished.emit(response)
            except Exception as e:
                self.error.emit(str(e))
    
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    
    # Question widget
    question_widget = create_question_widget(widget, api_client)
    layout.addWidget(question_widget)
    
    # Store references
    widget.question_widget = question_widget
    widget.api_client = api_client
    widget.current_worker = None
    
    # Connect signals
    def on_ask_clicked():
        question = widget.question_widget.question_input.toPlainText().strip()
        if not question:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("Please enter a question.")
            msg.exec()
            return
        
        # Disable button and show loading
        widget.question_widget.ask_button.setEnabled(False)
        widget.question_widget.answer_content.setText("Thinking...")
        widget.question_widget.confidence_label.setText("Confidence: ...")
        widget.question_widget.evidence_summary_label.setText("Evidence: ...")
        clear_answer(widget.question_widget)
        
        # Start worker thread
        widget.current_worker = AskWorker(api_client, question)
        
        def on_finished(response):
            update_answer(widget.question_widget, response)
            widget.question_widget.ask_button.setEnabled(True)
            widget.current_worker = None
        
        def on_error(error_msg):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(f"Error:\n{error_msg}")
            msg.exec()
            widget.question_widget.answer_content.setText(f"Error: {error_msg}")
            widget.question_widget.ask_button.setEnabled(True)
            widget.current_worker = None
        
        widget.current_worker.finished.connect(on_finished)
        widget.current_worker.error.connect(on_error)
        widget.current_worker.start()
    
    def on_show_evidence():
        is_visible = widget.question_widget.evidence_frame.isVisible()
        widget.question_widget.evidence_frame.setVisible(not is_visible)
        widget.question_widget.show_evidence_button.setText(
            "Hide Evidence" if not is_visible else "Show Evidence"
        )
    
    widget.question_widget.ask_button.clicked.connect(on_ask_clicked)
    widget.question_widget.show_evidence_button.clicked.connect(on_show_evidence)
    
    return widget
