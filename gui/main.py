"""
Librarian GUI - Main Application

A lightweight GUI client that communicates exclusively with the Librarian REST API.
This client never imports core/*, storage/*, parsers/*, or extractors/*.
"""

import sys
import os

# Check for PySide6 first, fallback to tkinter
USE_PYSIDE = False
USE_TKINTER = False

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    USE_PYSIDE = True
except ImportError:
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        USE_TKINTER = True
    except ImportError:
        pass

from gui.api_client import LibrarianAPIClient, get_client


def main():
    """Main entry point for Librarian GUI."""

    # Check if any GUI is available
    if not USE_PYSIDE and not USE_TKINTER:
        print("ERROR: No GUI library available.")
        print("Please install PySide6:")
        print("  pip install PySide6")
        print("Or ensure tkinter is installed with your Python.")
        print()
        print("You can still test the API client directly:")
        print("  python -c 'from gui.api_client import LibrarianAPIClient; print(LibrarianAPIClient().get_stats())'")
        sys.exit(1)

    # Get API URL from environment or use default
    api_url = os.environ.get("API_URL", "http://localhost:8000")

    # Initialize API client
    api_client = get_client(api_url)

    # Check API availability
    try:
        api_client.health_check()
    except Exception as e:
        print(f"Warning: Could not connect to API at {api_url}: {e}")
        print("The GUI will still start but may not function properly.")

    if USE_PYSIDE:
        run_pyside_app(api_client)
    elif USE_TKINTER:
        run_tkinter_app(api_client)


def run_pyside_app(api_client):
    """Run the GUI using PySide6."""
    from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
    from PySide6.QtCore import Qt, QTimer
    from gui.views.dashboard import create_dashboard_view, load_stats
    from gui.views.ask import create_ask_view
    from gui.views.timeline import create_timeline_view
    from gui.views.operations import create_operations_view

    app = QApplication(sys.argv)
    app.setApplicationName("Librarian Operations Console")

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Librarian Operations Console")
    window.setMinimumSize(1200, 800)

    # Create central widget with tabs
    central_widget = QWidget()
    window.setCentralWidget(central_widget)

    layout = QVBoxLayout(central_widget)

    # Create tabs
    tabs = QTabWidget()
    tabs.setStyleSheet("""
        QTabWidget::pane {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
        }
        QTabBar::tab {
            padding: 10px 20px;
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-bottom: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        QTabBar::tab:selected {
            background-color: white;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background-color: #e5e5e5;
        }
    """)

    # Operations tab (first - primary for developers/operators)
    operations_view = create_operations_view(tabs, api_client)
    tabs.addTab(operations_view, "Operations")

    # Dashboard tab
    dashboard_view = create_dashboard_view(tabs, api_client)
    tabs.addTab(dashboard_view, "Dashboard")

    # Ask tab
    ask_view = create_ask_view(tabs, api_client)
    tabs.addTab(ask_view, "Ask")

    # Timeline tab
    timeline_view = create_timeline_view(tabs, api_client)
    tabs.addTab(timeline_view, "Timeline")

    layout.addWidget(tabs)

    # Load initial dashboard data
    def load_initial_dashboard():
        load_stats(dashboard_view, api_client)

    QTimer.singleShot(100, load_initial_dashboard)

    # Show window
    window.show()

    # Run event loop
    sys.exit(app.exec())


def run_tkinter_app(api_client):
    """Run a simple GUI using tkinter (fallback)."""
    root = tk.Tk()
    root.title("Librarian Operations Console")
    root.geometry("800x600")

    # Create notebook (tabs)
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)

    # Dashboard tab
    dashboard_frame = tk.Frame(notebook)
    notebook.add(dashboard_frame, text="Dashboard")

    tk.Label(
        dashboard_frame,
        text="Library Statistics",
        font=("Arial", 16, "bold")
    ).pack(pady=10)

    # Stats labels
    stats_labels = {}
    for key in ["Library Root", "Documents", "Entities", "Events", "Locations"]:
        frame = tk.Frame(dashboard_frame, relief=tk.RAISED, borderwidth=1)
        frame.pack(pady=5, padx=20, fill='x')
        tk.Label(frame, text=key, font=("Arial", 10), fg="gray").pack()
        label = tk.Label(frame, text="Loading...", font=("Arial", 14, "bold"))
        label.pack()
        stats_labels[key] = label

    # Load stats button
    def load_stats():
        try:
            stats = api_client.get_stats()
            stats_labels["Library Root"].set(stats.get("library_root", "N/A"))
            stats_labels["Documents"].set(stats.get("documents", {}).get("total", 0))
            stats_labels["Entities"].set(stats.get("entities", {}).get("total", 0))
            stats_labels["Events"].set(stats.get("events", {}).get("total", 0))
            stats_labels["Locations"].set(stats.get("locations", {}).get("total", 0))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load stats:\n{e}")

    tk.Button(
        dashboard_frame,
        text="Refresh",
        command=load_stats
    ).pack(pady=10)

    # Ask tab
    ask_frame = tk.Frame(notebook)
    notebook.add(ask_frame, text="Ask")

    tk.Label(
        ask_frame,
        text="Ask a question about your library:",
        font=("Arial", 12, "bold")
    ).pack(pady=5)

    question_entry = tk.Text(ask_frame, height=3)
    question_entry.pack(pady=5, padx=20, fill='x')

    answer_label = tk.Label(ask_frame, text="", wraplength=700, justify='left')
    answer_label.pack(pady=10, padx=20, fill='both', expand=True)

    def ask_question():
        question = question_entry.get("1.0", tk.END).strip()
        if not question:
            messagebox.showwarning("Warning", "Please enter a question.")
            return

        try:
            response = api_client.ask_question(question)
            answer = response.get("answer", {})
            confidence = answer.get("confidence", 0)
            text = answer.get("text", "No answer available.")
            answer_label.config(text=f"Answer: {text}\n\nConfidence: {confidence:.2%}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to ask question:\n{e}")

    tk.Button(ask_frame, text="Ask", command=ask_question).pack(pady=5)

    # Timeline tab
    timeline_frame = tk.Frame(notebook)
    notebook.add(timeline_frame, text="Timeline")

    tk.Label(
        timeline_frame,
        text="Timeline",
        font=("Arial", 14, "bold")
    ).pack(pady=10)

    # Filters
    filter_frame = tk.Frame(timeline_frame)
    filter_frame.pack(pady=5)

    tk.Label(filter_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5)
    start_entry = tk.Entry(filter_frame)
    start_entry.grid(row=0, column=1, padx=5)

    tk.Label(filter_frame, text="End Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5)
    end_entry = tk.Entry(filter_frame)
    end_entry.grid(row=0, column=3, padx=5)

    # Timeline treeview
    tree_frame = tk.Frame(timeline_frame)
    tree_frame.pack(fill='both', expand=True, padx=20, pady=10)

    tree = ttk.Treeview(tree_frame, columns=("timestamp", "type", "description"), show='headings')
    tree.heading("timestamp", text="Timestamp")
    tree.heading("type", text="Event Type")
    tree.heading("description", text="Description")
    tree.column("timestamp", width=150)
    tree.column("type", width=100)
    tree.column("description", width=500)
    tree.pack(fill='both', expand=True)

    def load_timeline():
        for item in tree.get_children():
            tree.delete(item)

        try:
            data = api_client.get_timeline(
                start=start_entry.get() or None,
                end=end_entry.get() or None
            )
            events = data.get("data", [])

            if not events:
                tree.insert("", 0, values=("No events", "-", "No events found"))

            for event in events:
                tree.insert("", 0, values=(
                    event.get("timestamp", "-")[:19],
                    event.get("event_type", "-"),
                    event.get("description", "-")
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load timeline:\n{e}")

    tk.Button(timeline_frame, text="Refresh", command=load_timeline).pack(pady=5)

    # Load initial data
    load_stats()

    root.mainloop()


if __name__ == "__main__":
    main()
