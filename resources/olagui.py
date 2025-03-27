
from PySide6.QtCore import QCoreApplication, QSize, QThreadPool, QTimer, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QLabel, QMainWindow, \
    QVBoxLayout, \
    QApplication, QStatusBar, QGroupBox, QLineEdit, QGridLayout, QPushButton, QInputDialog, QComboBox, QMenu, QMessageBox, QCheckBox, QScrollArea, QSplashScreen, QTextBrowser, QDialog, QFileDialog

class GhStyle:
    STYLE_QLABEL_TITLE = "QLabel{ border-width: 1px; border-style: dotted; border-color: darkblue; font-weight: bold;}"
    STYLE_QLABEL_BOLD = "QLabel{ font-weight: bold;}"
    STYLE_QLABEL_EXTRAINFO = "QLabel{font: italic;color: gray;}"
    STYLE_QLABEL_EXTRAINFO_RIGHT = "QLabel{font: italic;color: gray;qproperty-alignment: AlignRight;}"
    STYLE_QLABEL_COMMENT = "border-width: 1px; border-style: dotted; border-color: gray;"

    STYLE_QCOMBO_EDITABLE = "QComboBox{border-width: 2px; border-style: outset; border-color: lightgray; font-weight: bold}"

    STYLE_QLINE_EDITABLE = "QLineEdit{border-width: 2px; border-style: outset; border-color: lightgray; font-weight: bold}"
    STYLE_QLINE_EDITED = "QLineEdit{border-width: 2px; border-style: outset; border-color: red; background-color: white; font-weight: bold}"

    STYLE_QPUSH_VOID = "QPushButton {border: 0px;}"

class GhGui:
    """
    some wording :
    "panel" -> QWidget / Container
    """
    @staticmethod
    def setupLayout(panel, layout, margin=0):
        """
        same as createContainerPanel but tu apply
        style on already existent widget
        :param panel QWidget
        :param layout to attach to the panel
        :return: panel ( QWidget )
        """
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(0)
        panel.setLayout(layout)
        return panel

    @staticmethod
    def createContainerPanel(layout, margin=0):
        """
        :param layout to attach to the panel
        :return: panel ( QWidget )
        """
        return GhGui.setupLayout(QWidget(), layout, margin=margin)

    @staticmethod
    def createToolbarButton(label, tip, icon, action):
        button = QPushButton(label)
        button.setStatusTip(tip)
        button.setIcon(icon)
        button.setIconSize(QSize(24, 24))
        button.clicked.connect(action)
        return button

    @staticmethod
    def createDefaultButton(label, tip, icon, action):
        button = QPushButton(label)
        button.setStatusTip(tip)
        button.setIcon(icon)
        button.setIconSize(QSize(16, 16))
        if action is not None:
            button.clicked.connect(action)
        return button

    @staticmethod
    def createLineEdit( initialValue, textChangedAction, editFinishedAction, width=None, style=None):
        line = QLineEdit()
        if width is not None:
            line.setFixedWidth(500)
        line.setText(initialValue)
        if style is not None:
            line.setStyleSheet(GhStyle.STYLE_QLINE_EDITABLE)
        line.textChanged.connect(textChangedAction)
        line.editingFinished.connect(editFinishedAction)
        return line
