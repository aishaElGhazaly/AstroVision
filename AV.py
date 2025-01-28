from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFrame, QVBoxLayout, QLabel, QTabWidget, QWidget, QPushButton, QGridLayout, QTabBar
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import sys

from search import Search
from quick_look import QuickLook
from fits_retrieval import FITSRetrieval
from composite_creation import CompositeCreation
from spectrogram_inspector import SpectrogramInspector
from image_enhancement import ImageEnhancement

class AstroVision(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AstroVision")
        self.setWindowIcon(QIcon("icon.png"))
        self.setGeometry(100, 100, 1280, 720)
        self.showMaximized()

        # Main frame
        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet("background-color: #2B2B2B;")
        self.setCentralWidget(self.main_frame)

        # Main layout
        main_layout = QVBoxLayout(self.main_frame)

        # Tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #5A5A5A;
                background-color: #2B2B2B;
            }
            QTabBar::tab {
                background-color: #3A3A3A;
                color: white;
                padding: 10px 20px;
                border: 1px solid #5A5A5A;
                border-radius: 5px;
                font-size: 14px;
                text-align: center;
                min-width: 150px;  /* Ensure wide tabs for text */
                max-width: 200px;
            }
            QTabBar::tab:selected {
                background-color: #5A9;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #4A8;
            }
        """)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tab_widget)

        # Create home tab
        self.create_home_tab()

    def create_home_tab(self):
        """Create the home tab."""
        home_tab = QWidget()
        layout = QVBoxLayout(home_tab)
        layout.setAlignment(Qt.AlignCenter)

        # Title
        title_label = QLabel("Welcome to AstroVision")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Cards for navigation
        cards_layout = QGridLayout()
        modules = [
            ("Search", self.open_search),
            ("Quick Look", self.open_quick_look),
            ("FITS Retrieval", self.open_fits_retrieval),
            ("Composite Creation", self.open_composite_creation),
            ("Image Enhancement", self.open_image_enhancement),
            ("Spectrogram Inspector", self.open_spectrogram_inspector)
        ]

        for i, (name, action) in enumerate(modules):
            card = QPushButton(name)
            card.setStyleSheet("""
                QPushButton {
                    background-color: #5A9;
                    color: white;
                    font-size: 22px;
                    font-weight: bold;
                    border: 1px solid #5A5A5A;
                    border-radius: 10px;
                    padding: 20px;
                }
                QPushButton:hover {
                    background-color: #4A8;
                }
            """)
            
            card.clicked.connect(action)
            card.setFixedSize(400, 200)
            
            cards_layout.addWidget(card, i // 3, i % 3)
        layout.addLayout(cards_layout)

        self.tab_widget.addTab(home_tab, "Home")

        # Disable close button for the home tab
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setTabButton(0, QTabBar.RightSide, None)  # Remove close button

    # In the AstroVision class:
    def open_search(self):
        """Open the Search module in a new tab."""
        search_tab = Search(self.tab_widget)
        self.tab_widget.addTab(search_tab, "Search")
        self.tab_widget.setCurrentWidget(search_tab)
    
    def open_quick_look(self):
        """Open the Quick Look module in a new tab."""
        quick_look_tab = QuickLook(self.tab_widget)
        self.tab_widget.addTab(quick_look_tab, "Quick Look")
        self.tab_widget.setCurrentWidget(quick_look_tab)
    
    def open_fits_retrieval(self):
        """Open the FITS Retrieval module in a new tab."""
        fits_retrieval_tab = FITSRetrieval(self.tab_widget)
        self.tab_widget.addTab(fits_retrieval_tab, "FITS Retrieval")
        self.tab_widget.setCurrentWidget(fits_retrieval_tab)
    
    def open_composite_creation(self):
        """Open the Composite Creation module in a new tab."""
        composite_creation_tab = CompositeCreation(self.tab_widget)
        self.tab_widget.addTab(composite_creation_tab, "Composite Creation")
        self.tab_widget.setCurrentWidget(composite_creation_tab)
    
    def open_image_enhancement(self):
        """Open the Image Enhancement module in a new tab."""
        image_enhancement_tab = ImageEnhancement(self.tab_widget)
        self.tab_widget.addTab(image_enhancement_tab, "Image Enhancement")
        self.tab_widget.setCurrentWidget(image_enhancement_tab)
    
    def open_spectrogram_inspector(self):
        """Open the Spectrogram Inspector module in a new tab."""
        spectro_inspector_tab = SpectrogramInspector(self.tab_widget)
        self.tab_widget.addTab(spectro_inspector_tab, "Spectrogram Inspector")
        self.tab_widget.setCurrentWidget(spectro_inspector_tab)
    
    def close_tab(self, index):
        """Close a tab."""
        if index > 0:  # Prevent closing the home tab
            self.tab_widget.removeTab(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(palette.Window, Qt.black)
    palette.setColor(palette.WindowText, Qt.white)
    app.setPalette(palette)

    window = AstroVision()
    window.show()
    sys.exit(app.exec_())