from PyQt5.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    open_module = pyqtSignal(str)


app_signals = AppSignals()
