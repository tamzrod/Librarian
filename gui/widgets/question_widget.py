"""
Question Widget for Ask View

Handles question input and answer display.
"""


def create_question_widget(parent, api_client):
    """Create question input and answer display widget."""
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
        QPushButton, QLabel, QFrame, QScrollArea
    )
    from PySide6.QtCore import Qt, QSize
    
    widget = QWidget(parent)
    main_layout = QVBoxLayout(widget)
    
    # Question input section
    input_frame = QFrame()
    input_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    input_layout = QVBoxLayout(input_frame)
    
    input_label = QLabel("Ask a question about your library:")
    input_label.setStyleSheet("font-size: 14px; font-weight: bold;")
    input_layout.addWidget(input_label)
    
    # Text input
    question_input = QTextEdit()
    question_input.setPlaceholderText("Where was the site visit on January 15 2026?")
    question_input.setMaximumHeight(80)
    question_input.setStyleSheet("""
        QTextEdit {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
        }
    """)
    input_layout.addWidget(question_input)
    
    # Ask button
    button_layout = QHBoxLayout()
    ask_button = QPushButton("Ask")
    ask_button.setFixedSize(QSize(100, 35))
    ask_button.setStyleSheet("""
        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #106ebe;
        }
        QPushButton:disabled {
            background-color: #ccc;
        }
    """)
    button_layout.addStretch()
    button_layout.addWidget(ask_button)
    input_layout.addLayout(button_layout)
    
    main_layout.addWidget(input_frame)
    
    # Answer section
    answer_frame = QFrame()
    answer_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    answer_layout = QVBoxLayout(answer_frame)
    
    answer_label = QLabel("Answer:")
    answer_label.setStyleSheet("font-size: 14px; font-weight: bold;")
    answer_layout.addWidget(answer_label)
    
    # Answer text (scrollable)
    answer_scroll = QScrollArea()
    answer_scroll.setWidgetResizable(True)
    answer_scroll.setMinimumHeight(150)
    
    answer_content = QLabel()
    answer_content.setWordWrap(True)
    answer_content.setStyleSheet("font-size: 14px; padding: 10px; background-color: #f9f9f9; border-radius: 5px;")
    answer_scroll.setWidget(answer_content)
    answer_layout.addWidget(answer_scroll)
    
    # Confidence
    confidence_label = QLabel("Confidence: -")
    confidence_label.setStyleSheet("font-size: 12px; color: #666;")
    answer_layout.addWidget(confidence_label)
    
    # Evidence summary
    evidence_summary_label = QLabel("Evidence: 0 items")
    evidence_summary_label.setStyleSheet("font-size: 12px; color: #666;")
    answer_layout.addWidget(evidence_summary_label)
    
    # Show Evidence button
    show_evidence_button = QPushButton("Show Evidence")
    show_evidence_button.setVisible(False)
    show_evidence_button.setStyleSheet("""
        QPushButton {
            background-color: #6c757d;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #5a6268;
        }
    """)
    answer_layout.addWidget(show_evidence_button)
    
    # Evidence details (hidden by default)
    evidence_frame = QFrame()
    evidence_frame.setVisible(False)
    evidence_layout = QVBoxLayout(evidence_frame)
    
    evidence_title = QLabel("Evidence Details:")
    evidence_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
    evidence_layout.addWidget(evidence_title)
    
    evidence_content = QLabel()
    evidence_content.setWordWrap(True)
    evidence_content.setStyleSheet("font-size: 12px; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
    evidence_layout.addWidget(evidence_content)
    
    answer_layout.addWidget(evidence_frame)
    
    main_layout.addWidget(answer_frame)
    main_layout.addStretch()
    
    # Store widgets for access
    widget.question_input = question_input
    widget.ask_button = ask_button
    widget.answer_content = answer_content
    widget.confidence_label = confidence_label
    widget.evidence_summary_label = evidence_summary_label
    widget.show_evidence_button = show_evidence_button
    widget.evidence_frame = evidence_frame
    widget.evidence_content = evidence_content
    widget.current_response = None
    
    return widget


def update_answer(widget, response: dict):
    """Update answer widget with new response."""
    widget.current_response = response
    
    answer = response.get("answer", {})
    widget.answer_content.setText(answer.get("text", "No answer available."))
    
    confidence = answer.get("confidence", 0)
    widget.confidence_label.setText(f"Confidence: {confidence:.2%}")
    
    evidence = response.get("evidence", {})
    total_evidence = (
        len(evidence.get("documents", [])) +
        len(evidence.get("entities", [])) +
        len(evidence.get("events", [])) +
        len(evidence.get("locations", [])) +
        len(evidence.get("relationships", []))
    )
    widget.evidence_summary_label.setText(f"Evidence: {total_evidence} items")
    
    trace = response.get("trace", [])
    widget.show_evidence_button.setVisible(len(trace) > 0)
    
    # Build evidence details
    if trace:
        details = []
        for item in trace[:10]:  # Show first 10
            source = item.get("source", "unknown")
            score = item.get("score", 0)
            reason = item.get("reason", "unknown")
            details.append(f"• {source} (score: {score}, reason: {reason})")
        widget.evidence_content.setText("\n".join(details))
    else:
        widget.evidence_content.setText("No trace information available.")


def clear_answer(widget):
    """Clear answer display."""
    widget.current_response = None
    widget.answer_content.setText("")
    widget.confidence_label.setText("Confidence: -")
    widget.evidence_summary_label.setText("Evidence: 0 items")
    widget.show_evidence_button.setVisible(False)
    widget.evidence_frame.setVisible(False)
