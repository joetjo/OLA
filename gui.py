# Copyright 2024 joetjo https://github.com/joetjo/OLA
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging
from datetime import datetime

from PySide6.QtCore import QCoreApplication, QSize, QThreadPool
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QLabel, QMessageBox, QMainWindow, \
    QVBoxLayout, \
    QApplication, QStatusBar, QToolBar, QComboBox, QFileDialog, QGroupBox, QLineEdit, QGridLayout

from resources.resources import Icons
from sbsgl.core.procevent import EventListener
from sbsgl.sbsgl import SBSGL
from tools import MdReportGenerator, FileUsageGenerator
from version import OLAVersionInfo


class OLAGuiSetup:
    POSX = 400
    POSY = 1500


class OLAGui:
    APP = None
    PLAYING_PANEL = None


class OLABackend:
    SBSGL = None


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
        bExit.triggered.connect(OLAGui.APP.shutdown)
        self.addAction(bExit)


class OLAStatusBar(QStatusBar):

    def __init__(self):
        super().__init__()

    def set(self, message):
        self.showMessage("{} | {}".format(datetime.now().strftime("%H:%M:%S"), message))


class OLAPlayingPanel(QGroupBox):
    def __init__(self):
        super().__init__()

        OLAGui.PLAYING_PANEL = self

        layout = QHBoxLayout()
        self.setLayout(layout)

        label = QLabel("playing panel")
        layout.addWidget(label)

        self.game = QLabel("-")
        layout.addWidget(self.game)

    def refresh(self):
        game = OLABackend.SBSGL.procmgr.getCurrentGame()
        if game is not None:
            self.game.setText(game.getName())
        else:
            self.game.setText("")


class OLAGameSessions(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel("Game Session panel")
        layout.addWidget(label)


class OLAObsidianAssistant(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel("Obsidian Assistant panel")
        layout.addWidget(label)


class OLATabPanel(QTabWidget):

    def __init__(self):
        super().__init__()

        self.setTabPosition(QTabWidget.North)
        self.setMovable(True)

        self.addTab(OLAObsidianAssistant(), "Assistant")
        self.addTab(OLAGameSessions(), "Sessions")


class OLAMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Obsidian Launcher Assistant - {}".format(OLAVersionInfo.CURRENT))

        self.move(OLAGuiSetup.POSX, OLAGuiSetup.POSY)

        self.toolbar = OLAToolbar("Main toolbar", self)
        self.addToolBar(self.toolbar)

        self.status = OLAStatusBar()
        self.setStatusBar(self.status)
        self.status.set("Loading in progress...")

        layout = QVBoxLayout()

        self.playingPanel = OLAPlayingPanel()
        layout.addWidget(self.playingPanel)

        self.tabPanel = OLATabPanel()
        layout.addWidget(self.tabPanel)

        mainWidget = QWidget()
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

        logging.info("OLAMainWindow - Main window ready")

    def setStatus(self, message):
        self.status.set(message)


class SbsglListener(EventListener):
    def newGame(self, game):
        pass

    def endGame(self, proc):
        pass

    def refreshDone(self, current_game, platform_list_updated, others):
        OLAGui.PLAYING_PANEL.refresh()


class OLAApplication(QApplication):

    def __init__(self, argv):
        super().__init__(argv)

        Icons.initIcons()

        OLAGui.APP = self
        self.setQuitOnLastWindowClosed(True)
        self.setWindowIcon(Icons.APP)
        self.main = OLAMainWindow()
        self.threadpool = QThreadPool()
        logging.info("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    def start(self):
        # self.startReporting()
        OLABackend.SBSGL = SBSGL()
        OLABackend.SBSGL.procmgr.setListener(SbsglListener())
        self.main.show()
        self.exec()

    def shutdown(self):
        QCoreApplication.quit()

    def startReporting(self):
        mdgen = MdReportGenerator()
        mdgen.signals.md_report_generation_finished.connect(self.mdReportsGenerated)
        mdgen.signals.md_last_report.connect(self.mdReportsStarted)
        self.threadpool.start(mdgen)

        filegen = FileUsageGenerator()
        filegen.signals.file_usage_generation_finished.connect(self.fileUsageGenerated)
        self.threadpool.start(filegen)

    def mdReportsStarted(self, reportName):
        self.main.setStatus("Processing {}".format(reportName))

    def mdReportsGenerated(self):
        self.main.setStatus("Markdown reports Generated")

    def fileUsageGenerated(self):
        self.main.setStatus("File usage Generated")
