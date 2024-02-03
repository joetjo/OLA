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

import sys
import logging
from datetime import datetime, timedelta

from PySide6.QtCore import QCoreApplication, QSize, QThreadPool, QTimer, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QLabel, QMainWindow, \
    QVBoxLayout, \
    QApplication, QStatusBar, QToolBar, QGroupBox, QLineEdit, QGridLayout, QPushButton, QInputDialog

from base.formatutil import FormatUtil
from base.osutil import OSUtil
from resources.resources import Icons
from sbsgl.sbsgl import SBSGL
from sbsgl.tools import MdReportGenerator, FileUsageGenerator, SgSGLProcessScanner, OLABackend

class OLAVersionInfo:
    VERSION = "2024.next.1"
    PREVIOUS = ""


class OLASetup:
    LOG_LEVEL = logging.INFO
    LOG_FILENAME = "ola.log"


logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', filename=OLASetup.LOG_FILENAME, filemode='w', level=OLASetup.LOG_LEVEL)

print("Obsidian Launcher Assistant - logging initialized (log file: {})".format(OLASetup.LOG_FILENAME))


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

    def __init__(self, name):
        super().__init__(name)
        self.setIconSize(QSize(24, 24))

        bRefresh = QAction("Check running process", self)
        bRefresh.setStatusTip("Scan now to detect game process running")
        bRefresh.setIcon(Icons.REFRESH)
        bRefresh.triggered.connect(OLAGui.APP.startProcessCheck)
        self.addAction(bRefresh)

        bGen = QAction("Generate vault reports", self)
        bGen.setStatusTip("Generate Markdown report and file usage")
        bGen.setIcon(Icons.SMALL_DOCUMENT)
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
        self.gameIcon = QLabel()
        self.gameIcon.setPixmap(Icons.VOID)
        leftPanelLayout.addWidget(self.gameIcon, 0, 0, Qt.AlignTop)
        leftPanelLayout.addWidget(QLabel("Playing"), 0, 1)
        leftPanelLayout.addWidget(QLabel(":"), 0, 2)
        self.game = QLabel("")
        self.game.setMinimumWidth(OLAGuiSetup.GAME_NAME_MIN_WIDTH)
        leftPanelLayout.addWidget(self.game, 0, 3)

        self.ptimeIcon = QLabel()
        self.ptimeIcon.setPixmap(Icons.VOID)
        leftPanelLayout.addWidget(self.ptimeIcon, 1, 0)
        leftPanelLayout.addWidget(QLabel("Since"), 1, 1)
        leftPanelLayout.addWidget(QLabel(":"), 1, 2)
        self.ptime = QLabel("")
        self.ptime.setMinimumWidth(OLAGuiSetup.GAME_NAME_MIN_WIDTH)
        leftPanelLayout.addWidget(self.ptime, 1, 3)

        self.layout().addWidget(leftPanel)

        # TODO RIGHT PANEL - Search and filtering
        rightPanel = QWidget()
        rightPanel.setLayout(leftPanelLayout)

        self.layout().addWidget(rightPanel)

        self.layout().addStretch()

    def refresh(self):
        game = OLABackend.SBSGL.procmgr.getCurrentGame()
        if game is not None:
            if game.getName() != self.game.text():
                self.game.setText(game.getName())
                self.gameIcon.setPixmap(Icons.PLAY)
                current_time = datetime.now()
                formatted_time = current_time.strftime('%H:%M:%S')
                self.ptime.setText(formatted_time)
                self.ptimeIcon.setPixmap(Icons.RUNNING)
        elif self.game.text() != "":
            self.gameIcon.setPixmap(Icons.VOID)
            self.game.setText("")
            self.ptimeIcon.setPixmap(Icons.VOID)
            self.ptime.setText("")

    def gameLaunchFailure(self):
        self.game.setText("")
        self.game.setPixmap(Icons.KO)


class OLAGameLine(QWidget):
    def __init__(self, row, layout, linkVault=False):
        super().__init__()

        self.vaultPath = None
        self.session = None
        self.sheet = None
        self.linkVault = linkVault

        self.name = QLabel()
        layout.addWidget(self.name, row, 0)

        self.playDuration = QLabel()
        layout.addWidget(self.playDuration, row, 1)

        self.playLastDuration = QLabel()
        layout.addWidget(self.playLastDuration, row, 2)

        bPanel = QWidget()
        bPanel.setLayout(QHBoxLayout())
        bPanel.layout().setContentsMargins(0, 0, 0, 0)
        bPanel.layout().addStretch()
        self.bVault = QPushButton("")
        self.bVault.setStatusTip("Open in obsidian Vault")
        self.bVault.setIcon(Icons.OBSIDIAN)
        self.bVault.clicked.connect(self.openInVault)
        bPanel.layout().addWidget(self.bVault)
        self.bVault.setVisible(False)

        if linkVault:
            self.bLink = QPushButton("")
            self.bLink.setStatusTip("Name in obsidian Vault")
            self.bLink.setIcon(Icons.PENCIL)
            self.bLink.clicked.connect(self.setVaultName)
            bPanel.layout().addWidget(self.bLink)
            self.bLink.setVisible(False)

        self.bStart = QPushButton("")
        self.bStart.setStatusTip("Start game")
        self.bStart.setIcon(Icons.START)
        self.bStart.clicked.connect(self.startGame)
        bPanel.layout().addWidget(self.bStart)
        self.bStart.setVisible(False)

        self.bPop = QPushButton("")
        self.bPop.setStatusTip("Start game")
        self.bPop.setIcon(Icons.POPMENU)
        self.bPop.clicked.connect(self.popMenu)
        bPanel.layout().addWidget(self.bPop)
        self.bPop.setVisible(False)

        layout.addWidget(bPanel, row, 3)

    def popMenu(self):
        pass  # TODO remove, exclude ...

    def startGame(self):
        OLABackend.SBSGL.launchGame(self.session, OLAGui.APP)

    def openInVault(self):
        if self.vaultPath is None:
            self.vaultPath = "{}%2F{}".format(OLABackend.VAULT.VAULT.replace(" ", "%20").replace("\\", "%2F"),
                                              self.sheet).replace(" ", "%20")
        url = "obsidian://open?path={}".format(self.vaultPath)
        logging.info("opening {}".format(url))
        OSUtil.systemOpen(url)

    def setVaultName(self):
        text, ok = QInputDialog.getText(self, "Obsidian sheet name",
                                        "name:", QLineEdit.Normal,
                                        self.sheet)
        if ok and text:
            self.session.getGameInfo()['sheet'] = text
        OLABackend.SBSGL.procmgr.storage.save()

    def setSession(self, session):
        """
        :param: session: sbsbl.data.session
        """
        self.session = session
        self.sheet = session.getGameInfo()['sheet']
        if len(self.sheet) > 0:
            self.name.setText(self.sheet)
        else:
            self.name.setText(session.getName())
        self.playDuration.setText(FormatUtil.formatDuration(session.getGameInfo()['duration']))
        self.playLastDuration.setText(FormatUtil.formatDuration(session.getGameInfo()['last_duration']))
        self.bVault.setVisible(True)
        self.bPop.setVisible(True)
        self.bVault.setEnabled(len(self.sheet) > 0)
        self.bStart.setVisible(True)
        self.bStart.setEnabled(True)
        if self.linkVault:
            self.bLink.setVisible(True)

    def setPlaying(self, play):
        """
        :param play: MhMarkdownFile
        """
        self.vaultPath = str(play.path).replace(" ", "%20").replace("\\", "%2F")
        self.name.setText(play.name)
        session = OLABackend.SBSGL.procmgr.findSessionBySheetName(play.name)
        if session is None:
            self.bVault.setVisible(True)
            self.bStart.setVisible(True)
            self.bStart.setEnabled(False)
            self.bPop.setVisible(True)
        else:
            self.setSession(session)

    def reset(self):
        self.name.setText("")
        self.bVault.setVisible(False)
        self.bPop.setVisible(False)
        self.bStart.setVisible(False)
        if self.linkVault:
            self.bLink.setVisible(False)


class OLASharedGameListWidget(QWidget):
    def __init__(self, title=None, linkVault=False):
        super().__init__()
        layout = QGridLayout()
        self.setLayout(layout)

        self.col1 = QLabel()
        if title is None:
            self.col1.setText("Game")
        else:
            self.col1.setText(title)
        layout.addWidget(self.col1, 0, 0)
        layout.addWidget(QLabel("Total play time"), 0, 1)
        layout.addWidget(QLabel("Last play duration"), 0, 2)

        self.lines = []
        for idx in range(0, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.lines.append([])
            self.lines[idx].append(OLAGameLine(idx + 1, layout, linkVault=linkVault))


class OLAGameSessions(OLASharedGameListWidget):
    def __init__(self):
        super().__init__(linkVault=True)
        OLAGui.SESSIONS = self

    def loadSessions(self):
        sessions = OLABackend.SBSGL.procmgr.getSessions()
        count = len(sessions)
        current = 0
        if count > 0:
            logging.debug("OLAGameSessions:  Loading {} sessions :".format(count))
            for session in sessions:
                # TODO : test if matching filter
                if current < OLAGuiSetup.VISIBLE_SESSION_COUNT:
                    self.lines[current][0].setSession(session)
                    current = current + 1
        else:
            logging.debug("OLAGameSessions: no session to load")

        for idx in range(current, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.lines[current][0].reset()


class OLAObsidianAssistant(OLASharedGameListWidget):
    def __init__(self):
        super().__init__(title="Obsidian vault not parsed")
        OLAGui.ASSISTANT = self

    def loadPlaying(self):
        playing = OLABackend.VAULT.PLAY
        count = len(playing)
        current = 0
        if count > 0:
            logging.debug("OLAGameSessions:  Loading {} play in progress :".format(count))
            for play in playing:
                # TODO : test if matching filter
                if current < OLAGuiSetup.VISIBLE_SESSION_COUNT:
                    self.lines[current][0].setPlaying(OLABackend.VAULT.PLAY[play])
                    current = current + 1
        else:
            logging.debug("OLAGameSessions: no playing session to load")

        for idx in range(current, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.lines[current][0].reset()

    def vaultReportInProgress(self):
        self.col1.setText("Vault report generation in progress")

    def vaultParsingInProgress(self):
        self.col1.setText("Vault loading in progress")

    def vaultParsed(self):
        self.col1.setText("Vault: {} files, {} tags, {} in progress"
                          .format(len(OLABackend.VAULT.SORTED_FILES), len(OLABackend.VAULT.TAGS), len(OLABackend.VAULT.PLAY)))
        self.loadPlaying()


class OLATabPanel(QTabWidget):

    def __init__(self):
        super().__init__()

        self.setTabPosition(QTabWidget.North)
        self.setMovable(True)

        self.addTab(OLAGameSessions(), "Sessions")
        self.addTab(OLAObsidianAssistant(), "Assistant")


class OLAMainWindow(QMainWindow):
    def __init__(self, version):
        super().__init__()
        OLAGui.MAIN = self
        self.setWindowTitle("Obsidian Launcher Assistant - {}".format(version))

        self.move(OLAGuiSetup.POSX, OLAGuiSetup.POSY)

        self.toolbar = OLAToolbar("Main toolbar")
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

    def __init__(self, argv, version):
        super().__init__(argv)

        Icons.initIcons()

        OLAGui.APP = self
        self.setQuitOnLastWindowClosed(True)
        self.setWindowIcon(Icons.APP)
        self.main = OLAMainWindow(version)
        self.threadpool = QThreadPool()
        OLABackend.THPOOL = self.threadpool
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
        OLAGui.ASSISTANT.vaultReportInProgress()
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

    def gameLaunched(self):
        self.main.setStatus("Game started")
        self.startProcessCheck()

    def gameLaunchFailure(self):
        self.main.setStatus("Failed to start game")
        OLAGui.PLAYING_PANEL.gameLaunchFailure()

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

logging.info("OLAApplication - starting application execution")
app = OLAApplication(sys.argv, OLAVersionInfo.VERSION)
app.start()
logging.info("OLAApplication - application terminated")
