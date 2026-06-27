import math

# Global stylesheet for QSS styling to create a premium, dark-mode, glassy theme.
APP_STYLE = """
/* Main Window background */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #020617);
    color: #f1f5f9;
}

QDialog {
    background: #0f172a;
    color: #f1f5f9;
}

/* Titles and major text */
QLabel {
    color: #f1f5f9;
    font-family: "Outfit", "Inter", "Segoe UI", sans-serif;
}

/* Score board card styling (glassmorphism) */
QFrame#score_card {
    background-color: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
}

/* Panel card styling for question info */
QFrame#panel_card {
    background-color: rgba(15, 23, 42, 0.85);
    border: 2px solid #3b82f6;
    border-radius: 16px;
}

/* Turn label styling */
QLabel#turn_label {
    color: #38bdf8;
    font-weight: bold;
}

/* General Buttons */
QPushButton {
    background-color: #1e293b;
    border: 1px solid #475569;
    color: #f1f5f9;
    border-radius: 8px;
    padding: 8px 16px;
    font-family: "Inter", "Segoe UI", sans-serif;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #334155;
    border: 1px solid #64748b;
}

QPushButton:pressed {
    background-color: #0f172a;
}

/* Action buttons with highlight colors */
QPushButton#primary_btn {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
}
QPushButton#primary_btn:hover {
    background-color: #3b82f6;
    border: 1px solid #60a5fa;
}

QPushButton#no_winner_btn {
    background-color: #64748b;
    border: 1px solid #94a3b8;
}
QPushButton#no_winner_btn:hover {
    background-color: #475569;
    border: 1px solid #64748b;
}

/* Header label in setting screen */
QLabel#title_header {
    font-size: 24px;
    font-weight: bold;
    color: #38bdf8;
    margin-bottom: 10px;
}

/* Text Inputs and Combo Boxes */
QLineEdit, QComboBox, QSpinBox {
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 6px;
    color: #f8fafc;
    padding: 6px 10px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #3b82f6;
}

/* Checkbox styling */
QCheckBox {
    color: #cbd5e1;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #475569;
    border-radius: 4px;
    background-color: #1e293b;
}

QCheckBox::indicator:checked {
    background-color: #3b82f6;
    border: 1px solid #3b82f6;
    image: url(check_mark_placeholder); /* PySide handles icons beautifully, we can draw a check path */
}

/* Othello Cell Styles (Unowned - Gray) */
QPushButton#othello_cell_gray {
    background-color: #1e293b;
    border: 2px solid #334155;
    border-radius: 10px;
}

QPushButton#othello_cell_gray:hover {
    background-color: #2c3e50;
    border: 2px solid #58a6ff;
}

/* Grid Layout container */
QWidget#othello_grid_container {
    background-color: #0b0f19;
    border: 3px solid #1e293b;
    border-radius: 14px;
}
"""

def get_font_size(base_size: float, current_width: float, current_height: float, reference_width: float = 800, reference_height: float = 600) -> int:
    """
    Dynamically scales the font size based on the window's current dimensions compared to a reference size.
    Limits minimum font size to 8pt.
    """
    # Scale based on the geometric mean of width and height changes
    scale_x = current_width / reference_width
    scale_y = current_height / reference_height
    scale = math.sqrt(scale_x * scale_y)
    
    scaled_size = int(base_size * scale)
    return max(scaled_size, 8)

def get_cell_style_qss(color: str | None, is_hovered: bool = False) -> str:
    """
    Returns the inline QSS for an Othello cell button based on its state.
    If color is None, it is unowned (gray). If it's a hex color, we apply it.
    """
    padding_qss = "padding: 0px; margin: 0px;"
    if color is None:
        if is_hovered:
            return f"background-color: #2d3748; border: 2px solid #818cf8; border-radius: 8px; {padding_qss}"
        else:
            return f"background-color: #1e293b; border: 2px solid #334155; border-radius: 8px; {padding_qss}"
    else:
        # Owned cell. We give it a slight inner glow/shadow and white border.
        if is_hovered:
            return f"background-color: {color}; border: 3px solid #ffffff; border-radius: 8px; {padding_qss}"
        else:
            return f"background-color: {color}; border: 2px solid #ffffff; border-radius: 8px; {padding_qss}"
