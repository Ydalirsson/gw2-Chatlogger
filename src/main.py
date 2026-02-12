import sys

from PySide6 import QtCore, QtGui, QtWidgets

from .paths import resource_path
from .ui import MainWindow


def main() -> int:
    QtCore.QCoreApplication.setOrganizationName("gw2-chatlogger")
    QtCore.QCoreApplication.setApplicationName("gw2-chatlogger")

    app = QtWidgets.QApplication(sys.argv)
    icon_path = resource_path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    window = MainWindow()
    window.resize(900, 700)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
