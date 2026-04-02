from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

class ImageEnhancement(QWidget):
    def __init__(self, parent_tab_widget):
        super().__init__()
        self.parent_tab_widget = parent_tab_widget
        layout = QVBoxLayout(self)

        placeholder_label = QLabel("Coming Soon")
        placeholder_label.setStyleSheet("""
            color: white; 
            font-size: 24px; 
            font-weight: bold; 
            background-color: #2B2B2B;
            border: 1px solid #5A5A5A;
            padding: 20px;
        """)
        placeholder_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(placeholder_label)
