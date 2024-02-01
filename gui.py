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
from datetime import datetime, timedelta

from PySide6.QtCore import QCoreApplication, QSize, QThreadPool, QTimer, Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QLabel, QMessageBox, QMainWindow, \
    QVBoxLayout, \
    QApplication, QStatusBar, QToolBar, QComboBox, QFileDialog, QGroupBox, QLineEdit, QGridLayout

from resources.resources import Icons
from sbsgl.sbsgl import SBSGL
from tools import MdReportGenerator, FileUsageGenerator, SgSGLProcessScanner, OLABackend
from version import OLAVersionInfo


class OLAGuiSetup:
    POSX = 400
    POSY = 1500
    PROCESS_SCANNER_TIMER = 20 * 1000
    GAME_NAME_MIN_WIDTH = 150
    VISIBLE_SESSION_COUNT = 20


class OLAGui:
    APP = None
    MAIN = None
    PLAYING_PANEL = None
    SESSIONS = None
    ASSISTANT = None


class OLAToolbar(QToolBar):

    def __init__(self, name, mainWindow):
        super().__init__(name)
        self.setIconSize(QSize(24, 24))

        bRefresh = QAction("Check running process", self)
        bRefresh.setStatusTip("Scan now to detect game process running")
        bRefresh.setIcon(Icons.REFRESH)
        bRefresh.triggered.connect(OLAGui.APP.startProcessCheck)
        self.addAction(bRefresh)

        bGen = QAction("Generate vault reports", self)
        bGen.setStatusTip("Generate Markdown report and file usage")
        bGen.setIcon(Icons.DOCUMENT)
        bGen.triggered.connect(OLAGui.APP.startReporting)
        self.addAction(bGen)

        bGen = QAction("Load obsidian vault", self)
        bGen.setStatusTip("Parse content of Obsidian vault")
        bGen.setIcon(Icons.FOLDER)
        bGen.triggered.connect(OLAGui.APP.parseVault)
        self.addAction(bGen)

        bExit = QAction("Exit", self)
        bExit.setStatusTip("Don't know, maybe, stop the App")
        bExit.setIcon(Icons.EXIT)
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

        self.setLayout(QHBoxLayout())

        # LEFT PANEL - Current Game
        leftPanel = QWidget()
        leftPanelLayout = QGridLayout()
        leftPanel.setLayout(leftPanelLayout)

        # LEFT PANEL - LINE 1
        leftPanelLayout.addWidget(QLabel("Playing"), 0, 0, Qt.AlignTop)
        leftPanelLayout.addWidget(QLabel(":"), 0, 1)
        self.game = QLabel("")
        self.game.setMinimumWidth(OLAGuiSetup.GAME_NAME_MIN_WIDTH)
        leftPanelLayout.addWidget(self.game, 0, 2)

        leftPanelLayout.addWidget(QLabel("Play time"), 1, 0)
        leftPanelLayout.addWidget(QLabel(":"), 1, 1)
        self.ptime = QLabel("")
        self.ptime.setMinimumWidth(OLAGuiSetup.GAME_NAME_MIN_WIDTH)
        leftPanelLayout.addWidget(self.ptime, 1, 2)

        leftPanelLayout.addWidget(QLabel("Total time"), 2, 0)
        leftPanelLayout.addWidget(QLabel(":"), 2, 1)
        self.ttime = QLabel("")
        self.ttime.setMinimumWidth(OLAGuiSetup.GAME_NAME_MIN_WIDTH)
        leftPanelLayout.addWidget(self.ttime, 2, 2)

        self.layout().addWidget(leftPanel)

        # TODO RIGHT PANEL - Search and filtering
        rightPanel = QWidget()
        rightPanel.setLayout(leftPanelLayout)

        self.layout().addWidget(rightPanel)

        self.layout().addStretch()

    def refresh(self):
        game = OLABackend.SBSGL.procmgr.getCurrentGame()
        if game is not None:
            self.game.setText(game.getName())
            if game.process.hasData():
                self.ptime.setText(str(timedelta(seconds=float(game.process.getStoreEntry()["duration"]))))
            else:
                self.ptime.setText("")
        else:
            self.game.setText("")
            self.ptime.setText("")


class OLAGameLine(QWidget):
    def __init__(self, layout):
        super().__init__()

        self.label = QLabel()
        layout.addWidget(self.label)

    def setSession(self, session):
        self.label.setText(session.getName())

    def reset(self):
        self.label.setText("")


class OLAGameSessions(QWidget):
    def __init__(self):
        super().__init__()
        OLAGui.SESSIONS = self

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.sessions = []
        for idx in range(0, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.sessions.append([])
            self.sessions[idx].append(OLAGameLine(layout))
            layout.addWidget(self.sessions[idx][0])
        layout.addStretch()

    def loadSessions(self):
        sessions = OLABackend.SBSGL.procmgr.getSessions()
        count = len(sessions)
        current = 0
        if count > 0:
            logging.debug("OLAGameSessions:  Loading {} sessions :".format(count))
            for session in sessions:
                # TODO : test if matching filter
                if current < OLAGuiSetup.VISIBLE_SESSION_COUNT:
                    self.sessions[current][0].setSession(session)
                    current = current + 1
        else:
            logging.debug("OLAGameSessions: no session to load")

        for idx in range(current, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.sessions[current][0].reset()


class OLAObsidianAssistant(QWidget):
    def __init__(self):
        super().__init__()
        OLAGui.ASSISTANT = self

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel("Obsidian vault not parsed")
        layout.addWidget(self.label)

        layout.addStretch()

    def vaultParsingInProgress(self):
        self.label.setText("Vault loading in progress")

    def vaultParsed(self):
        self.label.setText("Vault: {} files, {} tags".format(len(OLABackend.VAULT.SORTED_FILES), len(OLABackend.VAULT.TAGS)))


class OLATabPanel(QTabWidget):

    def __init__(self):
        super().__init__()

        self.setTabPosition(QTabWidget.North)
        self.setMovable(True)

        self.addTab(OLAGameSessions(), "Sessions")
        self.addTab(OLAObsidianAssistant(), "Assistant")


class OLAMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        OLAGui.MAIN = self
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

        self.timer = QTimer()
        self.timer.setInterval(OLAGuiSetup.PROCESS_SCANNER_TIMER)
        self.timer.timeout.connect(self.startProcessCheck)
        self.timer.start()
        logging.info("Process scanner set to be executed every {}s".format(OLAGuiSetup.PROCESS_SCANNER_TIMER / 1000))

        self.scanInProgress = False

    def start(self):
        self.parseVault()
        OLABackend.SBSGL = SBSGL()
        self.startProcessCheck()
        self.main.show()
        self.exec()

    def startProcessCheck(self):
        if not self.scanInProgress:
            self.scanInProgress = True
            proc = SgSGLProcessScanner()
            proc.signals.refresh_finished.connect(self.scanFinished)
            self.threadpool.start(proc)
        else:
            OLAGui.MAIN.setStatus("/!\\ game process scan rejected")

    def shutdown(self):
        QCoreApplication.quit()

    def parseVault(self):
        OLAGui.ASSISTANT.vaultParsingInProgress()
        mdgen = MdReportGenerator(report=False)
        mdgen.signals.md_report_generation_finished.connect(self.mdParsed)
        self.threadpool.start(mdgen)

    def startReporting(self):
        OLAGui.ASSISTANT.vaultParsingInProgress()
        mdgen = MdReportGenerator()
        mdgen.signals.md_report_generation_finished.connect(self.mdParsed)
        mdgen.signals.md_last_report.connect(self.mdReportsStarted)
        self.threadpool.start(mdgen)

        filegen = FileUsageGenerator()
        filegen.signals.file_usage_generation_finished.connect(self.fileUsageGenerated)
        self.threadpool.start(filegen)

    def scanFinished(self):
        self.scanInProgress = False
        OLAGui.PLAYING_PANEL.refresh()
        OLAGui.SESSIONS.loadSessions()
        OLAGui.MAIN.setStatus("Game process scan done")

    def mdReportsStarted(self, reportName):
        self.main.setStatus("Processing {}".format(reportName))

    def mdParsed(self):
        self.main.setStatus("Vault parsed")
        OLAGui.ASSISTANT.vaultParsed()

    def mdReportsGenerated(self):
        self.main.setStatus("Vault reports Generated")
        OLAGui.ASSISTANT.vaultParsed()

    def fileUsageGenerated(self):
        self.main.setStatus("File usage Generated")
