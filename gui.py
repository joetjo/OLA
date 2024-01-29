import logging
from PySide6.QtCore import QCoreApplication, QSize, QThreadPool
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QLabel, QMessageBox, QMainWindow, \
    QVBoxLayout, \
    QApplication, QStatusBar, QToolBar, QComboBox, QFileDialog, QGroupBox, QLineEdit, QGridLayout

from tools import MdReportGenerator, FileUsageGenerator
from version import OLAVersionInfo


class OLAGui:
    APP = None


class OLAToolbar(QToolBar):

    def __init__(self, name, mainWindow):
        super().__init__(name)
        self.setIconSize(QSize(24, 24))

        bExit = QAction("Generate", self)
        bExit.setStatusTip("Generate Markdown report and file usage")
        #        bExit.setIcon(Icons.EXIT)
        bExit.triggered.connect(OLAGui.APP.startReporting)
        self.addAction(bExit)

        bExit = QAction("Exit", self)
        bExit.setStatusTip("Don't know, maybe, stop the App")
        #        bExit.setIcon(Icons.EXIT)
        #        bExit.triggered.connect(MainWindow.shutdown)
        self.addAction(bExit)


class OLAMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Obsidian Launcher Assistant - {}".format(OLAVersionInfo.CURRENT))

        self.setMinimumWidth(200)
        self.setMinimumHeight(150)
        self.move(10, 10)

        toolbar = OLAToolbar("Main toolbar", self)
        self.addToolBar(toolbar)

        layout = QVBoxLayout()

        self.tmp = QLabel("TEST")
        layout.addWidget(self.tmp)

        mainWidget = QWidget()
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

        logging.info("OLAMainWindow - Main window ready")


class OLAApplication(QApplication):

    def __init__(self, argv):
        super().__init__(argv)
        OLAGui.APP = self
        self.setQuitOnLastWindowClosed(True)
        self.main = OLAMainWindow()
        self.threadpool = QThreadPool()
        logging.info("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    def start(self):
        self.startReporting()
        self.main.show()
        self.exec()

    def startReporting(self):
        mdgen = MdReportGenerator()
        mdgen.signals.md_report_generation_finished.connect(self.mdReportsGenerated())
        self.threadpool.start(mdgen)

        filegen = FileUsageGenerator()
        filegen.signals.file_usage_generation_finished.connect(self.fileUsageGenerated)
        self.threadpool.start(filegen)

    def mdReportsGenerated(self):
        self.main.tmp.setText("Markdown reports Generated")

    def fileUsageGenerated(self):
        self.main.tmp.setText("File usage Generated")
