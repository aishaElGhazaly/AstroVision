import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QTabBar, QPushButton,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from theme import apply_theme, TEXT_MUTED
from signals import app_signals
from modules.home import HomeTab
from modules.search import Search
from modules.quick_look import QuickLook
from modules.fits_retrieval import FITSRetrieval
from modules.composite_creation import CompositeCreation
from modules.image_enhancement import ImageEnhancement
from modules.spectrogram_inspector import SpectrogramInspector


class AstroVision(QMainWindow):
    _MODULE_MAP = {
        "search":                (Search,               "Search"),
        "quick_look":            (QuickLook,            "Quick Look"),
        "fits_retrieval":        (FITSRetrieval,        "FITS Retrieval"),
        "composite_creation":    (CompositeCreation,    "Composite Creation"),
        "image_enhancement":     (ImageEnhancement,     "Image Enhancement"),
        "spectrogram_inspector": (SpectrogramInspector, "Spectrogram Inspector"),
    }
    _MULTI_TAB = {"quick_look", "composite_creation"}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AstroVision")
        self.setWindowIcon(QIcon("./assets/icon.png"))

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabBar().setElideMode(Qt.ElideNone)
        self.tab_widget.tabBar().setExpanding(False)
        self.tab_widget.setUsesScrollButtons(True)
        layout.addWidget(self.tab_widget)

        home = HomeTab(self.tab_widget)
        self.tab_widget.addTab(home, "Home")
        self.tab_widget.tabBar().setTabButton(0, QTabBar.RightSide, None)

        app_signals.open_module.connect(self.open_module_tab)

    def _make_close_btn(self) -> QPushButton:
        btn = QPushButton("\u2715")
        btn.setFixedSize(16, 16)
        btn.setContentsMargins(0, 0, 0, 0)
        btn.setStyleSheet(f"""
            QPushButton {{
                color: {TEXT_MUTED};
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
                font-size: 11px;
                qproperty-flat: true;
            }}
            QPushButton:hover {{
                color: white;
                background-color: #FF6B6B;
                border-radius: 3px;
            }}
        """)
        btn.clicked.connect(lambda: self._close_tab_by_btn(btn))
        return btn

    def _close_tab_by_btn(self, btn: QPushButton) -> None:
        bar = self.tab_widget.tabBar()
        for i in range(self.tab_widget.count()):
            if bar.tabButton(i, QTabBar.RightSide) is btn:
                if i > 0:
                    self.tab_widget.removeTab(i)
                return

    def open_module_tab(self, name: str):
        cls, label = self._MODULE_MAP[name]
        if name not in self._MULTI_TAB:
            for i in range(self.tab_widget.count()):
                if isinstance(self.tab_widget.widget(i), cls):
                    self.tab_widget.setCurrentIndex(i)
                    return
        tab = cls(self.tab_widget)
        idx = self.tab_widget.addTab(tab, label)
        self.tab_widget.tabBar().setTabButton(idx, QTabBar.RightSide, self._make_close_btn())
        self.tab_widget.setCurrentWidget(tab)

    def _close_tab(self, index: int):
        if index > 0:
            self.tab_widget.removeTab(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    window = AstroVision()
    window.showMaximized()
    sys.exit(app.exec_())
