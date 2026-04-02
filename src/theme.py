from PyQt5.QtWidgets import QApplication

BG_DARK      = "#0D1117"
SURFACE      = "#161B22"
ACCENT       = "#55AA99"
TEXT_MUTED   = "#8B949E"
TEXT_PRIMARY = "#E6EDF3"
BORDER       = "#30363D"
FONT_FAMILY  = "Segoe UI"

QSS = f"""
/* ── Base ── */
QMainWindow, QDialog {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
}}
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
}}
QFrame {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
}}

/* ── Tab widget ── */
QTabWidget::pane {{
    border: none;
    background-color: {BG_DARK};
}}
QTabWidget::tab-bar {{
    alignment: left;
}}
QTabBar {{
    background: transparent;
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 10px 25px;
    min-height: 30px;
    min-width: 0px;
    border: none;
    font-family: {FONT_FAMILY};
    font-size: 13px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    color: {TEXT_PRIMARY};
    border-bottom: 3px solid {ACCENT};
}}
QTabBar::tab:hover {{
    color: {TEXT_PRIMARY};
}}
QTabBar::close-button {{
    image: none;
    width: 0;
    height: 0;
}}

/* ── Inputs ── */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    color: {TEXT_PRIMARY};
    padding: 4px 8px;
    font-family: {FONT_FAMILY};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {ACCENT};
}}
QComboBox {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    color: {TEXT_PRIMARY};
    padding: 4px 8px;
    font-family: {FONT_FAMILY};
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT};
    selection-color: {BG_DARK};
}}

/* ── Labels ── */
QLabel {{
    color: {TEXT_PRIMARY};
    background: transparent;
    font-family: {FONT_FAMILY};
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    color: {TEXT_MUTED};
    padding: 6px 14px;
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: #1C2128;
    color: {TEXT_PRIMARY};
}}
QPushButton:pressed {{
    background-color: #0D1117;
}}
QPushButton[accent="true"] {{
    background-color: {ACCENT};
    border: none;
    color: {BG_DARK};
    font-weight: bold;
}}
QPushButton[accent="true"]:hover {{
    background-color: #66BBAA;
}}
QPushButton[accent="true"]:pressed {{
    background-color: #449988;
}}

/* ── Table ── */
QTableWidget {{
    background-color: {SURFACE};
    gridline-color: {BORDER};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    font-family: {FONT_FAMILY};
}}
QTableWidget::item:selected {{
    background-color: {ACCENT};
    color: {BG_DARK};
}}
QHeaderView::section {{
    background-color: {BG_DARK};
    color: {TEXT_MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px 8px;
    font-family: {FONT_FAMILY};
    font-size: 12px;
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: {BG_DARK};
    width: 8px;
    margin: 0;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {SURFACE};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {BORDER};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {BG_DARK};
    height: 8px;
    margin: 0;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {SURFACE};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {BORDER};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── Progress bar ── */
QProgressBar {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 4px;
    color: {TEXT_PRIMARY};
    text-align: center;
    font-family: {FONT_FAMILY};
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 4px;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background-color: {BORDER};
}}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(QSS)
