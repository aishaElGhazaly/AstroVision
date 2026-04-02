from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QGridLayout, QLabel,
    QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QPainterPath, QFontMetrics,
)
from PyQt5.QtCore import Qt, QRect, QRectF, QPointF

from signals import app_signals
from theme import ACCENT, SURFACE, BG_DARK, TEXT_PRIMARY, TEXT_MUTED, BORDER, FONT_FAMILY
from widgets.star_field import StarField


_MODULES = [
    ("search",                "Search",               "Query SDSS photometric catalog"),
    ("quick_look",            "Quick Look",           "Preview sky images by coordinates"),
    ("fits_retrieval",        "FITS Retrieval",       "Download & inspect FITS files"),
    ("composite_creation",    "Composite Creation",   "Build RGB images from FITS bands"),
    ("image_enhancement",     "Image Enhancement",    "Adjust and enhance imagery"),
    ("spectrogram_inspector", "Spectrogram Inspector","Explore SDSS spectral data"),
]


def _draw_icon(painter: QPainter, box: QRect, key: str) -> None:
    """Draw a white icon inside the given box rect."""
    cx = box.x() + box.width() // 2
    cy = box.y() + box.height() // 2

    pen = QPen(QColor(255, 255, 255))
    pen.setWidth(2)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if key == "search":
        r = 7
        painter.drawEllipse(cx - r - 2, cy - r, r * 2, r * 2)
        painter.drawLine(cx + r - 2, cy + r - 1, cx + r + 5, cy + r + 6)

    elif key == "quick_look":
        painter.drawEllipse(cx - 11, cy - 7, 22, 14)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(cx - 3, cy - 3, 6, 6)

    elif key == "fits_retrieval":
        # Downward arrow
        painter.drawLine(cx, cy - 9, cx, cy + 5)
        painter.drawLine(cx - 6, cy - 1, cx, cy + 7)
        painter.drawLine(cx + 6, cy - 1, cx, cy + 7)
        # Base line
        painter.drawLine(cx - 8, cy + 9, cx + 8, cy + 9)

    elif key == "composite_creation":
        # Three offset rectangles (layer stack)
        offsets = [(-5, -5), (-1, -1), (3, 3)]
        for ox, oy in offsets:
            painter.drawRect(cx + ox - 7, cy + oy - 6, 14, 10)

    elif key == "image_enhancement":
        # Equalizer / sliders: three horizontal lines with ticks
        positions = [
            (cy - 7, cx - 8, cx + 8, cx - 1),
            (cy,     cx - 8, cx + 8, cx + 3),
            (cy + 7, cx - 8, cx + 8, cx - 3),
        ]
        for ly, x1, x2, tx in positions:
            painter.drawLine(x1, ly, x2, ly)
            painter.drawLine(tx, ly - 4, tx, ly + 4)

    elif key == "spectrogram_inspector":
        path = QPainterPath()
        x0 = cx - 12
        path.moveTo(x0, cy)
        path.cubicTo(x0 + 3, cy - 10, x0 + 9, cy + 10, x0 + 12, cy)
        path.cubicTo(x0 + 15, cy - 10, x0 + 21, cy + 10, x0 + 24, cy)
        painter.drawPath(path)


class ModuleCard(QPushButton):
    def __init__(self, key: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self._module_key = key
        self._title = title
        self._description = description
        self._hovered = False

        self.setFixedSize(400, 175)
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setStyleSheet("background: transparent; border: none;")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 153))
        self.setGraphicsEffect(shadow)

        self.clicked.connect(lambda: app_signals.open_module.emit(self._module_key))

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        # Background
        bg_color = QColor(SURFACE)
        painter.setBrush(bg_color)
        if self._hovered:
            pen = QPen(QColor(ACCENT))
            pen.setWidthF(1.5)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, w, h), 16, 16)

        # Icon box — sits in the top-left with comfortable padding
        icon_box = QRect(20, 22, 44, 44)
        painter.setBrush(QColor(ACCENT))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(icon_box, 10, 10)

        # Icon
        _draw_icon(painter, icon_box, self._module_key)

        # Title — vertically centred alongside icon box
        title_font = QFont(FONT_FAMILY, 14)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor(TEXT_PRIMARY))
        title_x = icon_box.right() + 14
        painter.drawText(QRect(title_x, icon_box.top(), w - title_x - 16, icon_box.height()),
                         Qt.AlignVCenter | Qt.AlignLeft, self._title)

        # Description — below the icon row with room to breathe
        desc_font = QFont(FONT_FAMILY, 11)
        painter.setFont(desc_font)
        painter.setPen(QColor(TEXT_MUTED))
        desc_y = icon_box.bottom() + 16
        painter.drawText(QRect(20, desc_y, w - 40, h - desc_y - 16),
                         Qt.AlignTop | Qt.AlignLeft | Qt.TextWordWrap,
                         self._description)

        # Hover chevron
        if self._hovered:
            chev_font = QFont(FONT_FAMILY, 14)
            painter.setFont(chev_font)
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(QRect(0, 0, w - 16, h - 14),
                             Qt.AlignBottom | Qt.AlignRight, "\u203a")

        painter.end()


class HomeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Star field fills entire widget, behind everything
        self._star_field = StarField(self)
        self._star_field.resize(self.size())

        # Central content layout
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setSpacing(0)

        # Title
        title = QLabel("AstroVision")
        title_font = QFont(FONT_FAMILY)
        title_font.setPointSize(52)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {ACCENT}; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        outer.addWidget(title)

        outer.addSpacerItem(QSpacerItem(0, 6, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Subtitle
        subtitle = QLabel("Making astronomical data accessible.")
        sub_font = QFont(FONT_FAMILY, 13)
        subtitle.setFont(sub_font)
        subtitle.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        outer.addWidget(subtitle)

        outer.addSpacerItem(QSpacerItem(0, 56, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Module cards grid
        grid = QGridLayout()
        grid.setSpacing(20)
        grid.setAlignment(Qt.AlignCenter)

        for i, (key, title_text, desc) in enumerate(_MODULES):
            card = ModuleCard(key, title_text, desc)
            grid.addWidget(card, i // 3, i % 3)

        outer.addLayout(grid)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._star_field.resize(self.size())
