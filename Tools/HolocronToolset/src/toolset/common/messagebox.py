from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QObject, QThread, Signal
from qtpy.QtWidgets import QApplication, QMessageBox

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

HELPERS: list[MessageBoxHelper] = []

class MessageBoxHelper(QObject):
    about_signal = Signal(object, str, str)
    aboutQt_signal = Signal(object, str)
    critical_signal = Signal(object, str, str, object, object)
    warning_signal = Signal(object, str, str, object, object)
    question_signal = Signal(object, str, str, object, object)
    information_signal = Signal(object, str, str, object, object)
    exec_signal = Signal(QMessageBox)

    def __init__(self):
        super().__init__()
        self.about_signal.connect(self.show_about)
        self.aboutQt_signal.connect(self.show_aboutQt)
        self.critical_signal.connect(self.show_critical)
        self.warning_signal.connect(self.show_warning)
        self.question_signal.connect(self.show_question)
        self.information_signal.connect(self.show_information)

    @staticmethod
    def show_about(parent, title, text):
        assert QThread.currentThread() == QApplication.instance().thread()
        QMessageBox.about(parent, title, text)

    @staticmethod
    def show_aboutQt(parent, title):
        assert QThread.currentThread() == QApplication.instance().thread()
        QMessageBox.aboutQt(parent, title)

    @staticmethod
    def show_exec(messagebox: ThreadSafeQMessageBox):
        assert QThread.currentThread() == QApplication.instance().thread()
        messagebox.exec_()

    @staticmethod
    def show_critical(
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.NoButton,
    ):
        assert QThread.currentThread() == QApplication.instance().thread()
        QMessageBox.critical(parent, title, text, buttons, defaultButton)

    @staticmethod
    def show_warning(
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.NoButton,
    ):
        assert QThread.currentThread() == QApplication.instance().thread()
        QMessageBox.warning(parent, title, text, buttons, defaultButton)

    @staticmethod
    def show_question(
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.NoButton,
    ):
        assert QThread.currentThread() == QApplication.instance().thread()
        QMessageBox.question(parent, title, text, buttons, defaultButton)

    @staticmethod
    def show_information(
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.NoButton,
    ):
        assert QThread.currentThread() == QApplication.instance().thread()
        QMessageBox.information(parent, title, text, buttons, defaultButton)


class ThreadSafeQMessageBox:
    """Does not work yet. Have tried invokeMethod and QTimer.singleShot and signals, all occasionally cause crashes in pyqt5."""
    def __init__(self):
        self.helper: MessageBoxHelper = MessageBoxHelper()

    def exec(self):
        helper = MessageBoxHelper()
        HELPERS.append(helper)
        helper.exec_signal.emit(self)
        HELPERS.remove(helper)
    def exec_(self):
        return self.exec()

    @staticmethod
    def about(
        parent: QWidget | None,
        title: str,
        text: str,
    ):
        helper = MessageBoxHelper()
        HELPERS.append(helper)
        helper.about_signal.emit(parent, title, text)
        HELPERS.remove(helper)

    @staticmethod
    def aboutQt(
        parent: QWidget | None,
        title: str,
    ):
        helper = MessageBoxHelper()
        HELPERS.append(helper)
        helper.aboutQt_signal.emit(parent, title)
        HELPERS.remove(helper)

    @staticmethod
    def critical(  # noqa: PLR0913
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.NoButton,
    ):
        helper = MessageBoxHelper()
        HELPERS.append(helper)
        helper.critical_signal.emit(parent, title, text, buttons, defaultButton)
        HELPERS.remove(helper)

    @staticmethod
    def warning(  # noqa: PLR0913
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.NoButton,
    ):
        helper = MessageBoxHelper()
        HELPERS.append(helper)
        helper.warning_signal.emit(parent, title, text, buttons, defaultButton)
        HELPERS.remove(helper)

    @staticmethod
    def question(  # noqa: PLR0913
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.NoButton,
    ):
        helper = MessageBoxHelper()
        HELPERS.append(helper)
        helper.question_signal.emit(parent, title, text, buttons, defaultButton)
        HELPERS.remove(helper)

    @staticmethod
    def information(  # noqa: PLR0913
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.NoButton,
    ):
        helper = MessageBoxHelper()
        HELPERS.append(helper)
        helper.information_signal.emit(parent, title, text, buttons, defaultButton)
        HELPERS.remove(helper)

class Worker(QObject):
    def __init__(
        self,
        message_box: ThreadSafeQMessageBox,
    ):
        super().__init__()
        self.message_box: ThreadSafeQMessageBox = message_box

    def run(self):
        self.message_box.about(None, "Thread", "This is the 'about' dialog from a worker thread.")
        self.message_box.aboutQt(None, "Qt Version Information")
        self.message_box.critical(None, "Thread", "This is a 'critical' dialog from a worker thread.")
        self.message_box.warning(None, "Thread", "This is a 'warning' dialog from a worker thread.")
        self.message_box.question(None, "Thread", "This is a 'question' dialog from a worker thread.")
        self.message_box.information(None, "Thread", "This is an 'information' dialog from a worker thread.")

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    message_box = ThreadSafeQMessageBox()

    # Test in the main thread
    #message_box.about(None, "Main Thread", "This is the 'about' dialog from the main thread.")
    #message_box.aboutQt(None, "Qt Version Information")
    #message_box.critical(None, "Main Thread", "This is a 'critical' dialog from the main thread.")
    #message_box.warning(None, "Main Thread", "This is a 'warning' dialog from the main thread.")
    #message_box.question(None, "Main Thread", "This is a 'question' dialog from the main thread.")
    #message_box.information(None, "Main Thread", "This is an 'information' dialog from the main thread.")

    # Test in a new QThread
    worker = Worker(message_box)
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    thread.start()

    sys.exit(app.exec_())
