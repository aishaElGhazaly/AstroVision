import random
import math

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QPen
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF


class StarField(QWidget):
    """Animated star field background with depth layers and shooting stars."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)

        self._canvas_w = 1920
        self._canvas_h = 1080

        self._stars = self._generate_stars()
        self._shooting_stars = []

        # Twinkle timer — 50ms for smooth animation
        self._twinkle_timer = QTimer(self)
        self._twinkle_timer.timeout.connect(self._tick)
        self._twinkle_timer.start(50)

        # Shooting star scheduler
        self._shoot_timer = QTimer(self)
        self._shoot_timer.setSingleShot(True)
        self._shoot_timer.timeout.connect(self._spawn_shooting_star)
        self._schedule_next_shot()

        self.lower()

    # ── Generation ──────────────────────────────────────────────────────────

    def _generate_stars(self):
        stars = []
        layers = [
            # (count, size, opacity_min, opacity_max, speed_min, speed_max)
            (160, 1, 0.15, 0.50, 0.01, 0.02),
            (50,  2, 0.40, 0.80, 0.02, 0.04),
            (15,  3, 0.70, 1.00, 0.04, 0.07),
        ]
        for count, size, op_min, op_max, sp_min, sp_max in layers:
            for _ in range(count):
                opacity = random.uniform(op_min, op_max)
                speed = random.uniform(sp_min, sp_max)
                if random.random() < 0.5:
                    speed = -speed
                stars.append({
                    'rx': random.random(),
                    'ry': random.random(),
                    'size': size,
                    'opacity': opacity,
                    'twinkle_speed': speed,
                    'op_min': op_min,
                    'op_max': op_max,
                })
        return stars

    # ── Shooting stars ───────────────────────────────────────────────────────

    def _schedule_next_shot(self):
        self._shoot_timer.start(random.randint(8000, 12000))

    def _spawn_shooting_star(self):
        if not self._shooting_stars:
            angle_deg = random.uniform(20, 40)
            angle_rad = math.radians(angle_deg)
            # Start along top edge (left 80% of width) or left edge (top 50%)
            if random.random() < 0.7:
                sx_r = random.uniform(0.05, 0.75)
                sy_r = 0.0
            else:
                sx_r = 0.0
                sy_r = random.uniform(0.05, 0.45)
            total_dist = random.randint(320, 520)   # pixels to travel
            tail_len   = random.randint(80, 130)
            # speed: pixels per tick (50ms), target ~700-900ms lifetime
            speed_px = total_dist / random.randint(14, 18)
            self._shooting_stars.append({
                'sx_r': sx_r, 'sy_r': sy_r,
                'angle': angle_rad,
                'progress': 0.0,        # 0 → 1
                'total_dist': total_dist,
                'speed': speed_px,
                'tail_len': tail_len,
            })
        self._schedule_next_shot()

    # ── Animation tick ───────────────────────────────────────────────────────

    def _tick(self):
        w, h = self.width() or self._canvas_w, self.height() or self._canvas_h

        for star in self._stars:
            star['opacity'] += star['twinkle_speed']
            if star['opacity'] >= star['op_max']:
                star['opacity'] = star['op_max']
                star['twinkle_speed'] = -abs(star['twinkle_speed'])
            elif star['opacity'] <= star['op_min']:
                star['opacity'] = star['op_min']
                star['twinkle_speed'] = abs(star['twinkle_speed'])

        finished = []
        for ss in self._shooting_stars:
            ss['progress'] += ss['speed'] / ss['total_dist']
            if ss['progress'] >= 1.0:
                finished.append(ss)
        for ss in finished:
            self._shooting_stars.remove(ss)

        self.update()

    # ── Resize ───────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_w = event.size().width()
        new_h = event.size().height()
        if new_w > 0 and new_h > 0:
            self._canvas_w = new_w
            self._canvas_h = new_h

    # ── Paint ────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        w = self.width()
        h = self.height()
        if w == 0 or h == 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(0, 0, w, h, QColor("#0D1117"))

        # Stars
        painter.setPen(Qt.NoPen)
        for star in self._stars:
            x = int(star['rx'] * w)
            y = int(star['ry'] * h)
            s = star['size']
            alpha = int(star['opacity'] * 255)
            painter.setBrush(QColor(255, 255, 255, alpha))
            painter.drawEllipse(x - s // 2, y - s // 2, s, s)

        # Shooting stars
        for ss in self._shooting_stars:
            sx = ss['sx_r'] * w
            sy = ss['sy_r'] * h
            angle = ss['angle']
            total = ss['total_dist']
            tail_len = ss['tail_len']
            p = ss['progress']

            # Head travels the full total_dist over p=0→1
            travelled = p * total
            head_x = sx + math.cos(angle) * travelled
            head_y = sy + math.sin(angle) * travelled

            # Tail is a fixed length behind the head
            tail_x = head_x - math.cos(angle) * tail_len
            tail_y = head_y - math.sin(angle) * tail_len

            # Fade out over last 30% of lifetime
            fade = max(0.0, 1.0 - max(0.0, p - 0.7) / 0.3)
            head_alpha = int(230 * fade)

            grad = QLinearGradient(QPointF(head_x, head_y), QPointF(tail_x, tail_y))
            grad.setColorAt(0.0, QColor(255, 255, 255, head_alpha))
            grad.setColorAt(0.35, QColor(200, 230, 255, int(head_alpha * 0.5)))
            grad.setColorAt(1.0, QColor(255, 255, 255, 0))

            pen = QPen()
            pen.setBrush(grad)
            pen.setWidthF(1.5)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(head_x, head_y), QPointF(tail_x, tail_y))

        painter.end()
