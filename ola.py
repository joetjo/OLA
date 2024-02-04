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
import sys
from datetime import datetime
from pathlib import Path

import pyautogui
from PySide6.QtCore import QCoreApplication, QSize, QThreadPool, QTimer, Qt, QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QLabel, QMainWindow, \
    QVBoxLayout, \
    QApplication, QStatusBar, QToolBar, QGroupBox, QLineEdit, QGridLayout, QPushButton, QInputDialog, QComboBox, QMenu

from base.formatutil import FormatUtil
from resources.resources import Icons
from sbsgl.sbsgl import SBSGL
from sbsgl.tools import MdReportGenerator, FileUsageGenerator, SgSGLProcessScanner, OLABackend


class OLAVersionInfo:
    VERSION = "2024.02.03 alpha 3"
    PREVIOUS = ""


class OLASetup:
    LOG_LEVEL = logging.INFO
    LOG_FILENAME = "ola.log"


if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print("Starting in packaged mode (temp folder {})".format(Path(sys._MEIPASS)))

stdout = logging.StreamHandler(stream=sys.stdout)
fmt = logging.Formatter("%(asctime)s %(message)s")
stdout.setFormatter(fmt)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stdout)


class OLAGuiSetup:
    POSX = 400
    POSY = 1500
    PROCESS_SCANNER_TIMER = 20 * 1000
    GAME_NAME_MIN_WIDTH = 150
    VISIBLE_SESSION_COUNT = 20
    VISIBLE_TYPE_COUNT = 15
    STYLE_QLABEL_TITLE = "QLabel{ border-width: 1px; border-style: dotted; border-color: darkblue; font-weight: bold;}"


class OLAFilter:
    def __init__(self):
        self.type = None


class OLAGui:
    APP = None
    MAIN = None
    PLAYING_PANEL = None
    SESSIONS = None
    ASSISTANT = None
    FILTER = OLAFilter()


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
        bGen.setIcon(Icons.REPORT)
        bGen.triggered.connect(OLAGui.APP.startReporting)
        self.addAction(bGen)

        bGen = QAction("Load obsidian vault", self)
        bGen.setStatusTip("Parse content of Obsidian vault")
        bGen.setIcon(Icons.IMPORT)
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


class OLAPlayingPanel(QWidget):
    def __init__(self):
        super().__init__()

        OLAGui.PLAYING_PANEL = self

        self.sheet = None
        self.rawName = None
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
        self.bVault = QPushButton("")
        self.bVault.setStatusTip("Open in obsidian Vault")
        self.bVault.setIcon(Icons.OBSIDIAN)
        self.bVault.clicked.connect(self.openInVault)
        self.bVault.setVisible(False)
        leftPanelLayout.addWidget(self.bVault, 0, 4)

        self.ptimeIcon = QLabel()
        self.ptimeIcon.setPixmap(Icons.VOID)
        leftPanelLayout.addWidget(self.ptimeIcon, 1, 0)
        leftPanelLayout.addWidget(QLabel("Since"), 1, 1)
        leftPanelLayout.addWidget(QLabel(":"), 1, 2)
        self.ptime = QLabel("")
        self.ptime.setMinimumWidth(OLAGuiSetup.GAME_NAME_MIN_WIDTH)
        leftPanelLayout.addWidget(self.ptime, 1, 3)

        self.layout().addWidget(leftPanel)

        # Middle
        self.layout().addStretch()

        # TODO RIGHT PANEL - Search and filtering
        rightPanel = QGroupBox()
        rightPanelLayout = QGridLayout()
        rightPanel.setLayout(rightPanelLayout)

        self.filterType = QComboBox()
        self.filterType.setMaxVisibleItems(OLAGuiSetup.VISIBLE_TYPE_COUNT)
        self.filterType.currentTextChanged.connect(self.applyFilter)
        rightPanelLayout.addWidget(QLabel("#Type (Obsidian)"), 0, 0)
        rightPanelLayout.addWidget(QLabel(":"), 0, 1)
        rightPanelLayout.addWidget(self.filterType, 0, 2)

        self.layout().addWidget(rightPanel)

    def applyFilter(self):
        OLAGui.FILTER.type = self.filterType.currentText()
        if len(OLAGui.FILTER.type) == 0:
            OLAGui.FILTER.type = None
        OLAGui.ASSISTANT.vaultParsed()
        OLAGui.SESSIONS.loadSessions()

    def refreshVault(self):
        currentType = self.filterType.currentText()
        self.filterType.clear()
        self.filterType.addItem("")
        self.filterType.addItems(OLABackend.VAULT.TYPES)
        self.filterType.setCurrentText(currentType)
        count = len(OLABackend.VAULT.TYPES) + 1
        if count > OLAGuiSetup.VISIBLE_TYPE_COUNT:
            count = OLAGuiSetup.VISIBLE_TYPE_COUNT
        self.filterType.setMaxVisibleItems(count)

    def refreshSBSGL(self):
        game = OLABackend.SBSGL.procmgr.getCurrentGame()
        if game is not None:
            if game.getName() != self.rawName:
                self.rawName = game.getName()
                self.sheet = game.process.getStoreEntry()["sheet"]
                if len(self.sheet) == 0:
                    self.sheet = None
                    self.game.setText(game.getName())
                else:
                    self.game.setText(self.sheet)
                self.gameIcon.setPixmap(Icons.PLAY)
                current_time = datetime.now()
                formatted_time = current_time.strftime('%H:%M:%S')
                self.ptime.setText(formatted_time)
                self.ptimeIcon.setPixmap(Icons.RUNNING)
                self.bVault.setVisible(True)
        elif self.game.text() != "":
            self.gameIcon.setPixmap(Icons.VOID)
            self.game.setText("")
            self.ptimeIcon.setPixmap(Icons.VOID)
            self.ptime.setText("")
            self.bVault.setVisible(False)
            self.sheet = None

    def gameLaunchFailure(self):
        self.game.setText("Game not available")
        self.gameIcon.setPixmap(Icons.KO)

    def openInVault(self):
        OLABackend.openInVault(sheetName=self.sheet)


class OLAGameLine(QWidget):
    def __init__(self, row, layout, linkVault=False):
        super().__init__()

        self.vaultPath = None
        self.session = None
        self.sheet = None
        self.sheetFile = None
        self.linkVault = linkVault

        self.platform = QLabel()
        layout.addWidget(self.platform, row, 0)

        self.name = QLabel()
        layout.addWidget(self.name, row, 1)

        self.playDuration = QLabel()
        layout.addWidget(self.playDuration, row, 2)

        self.playLastDuration = QLabel()
        layout.addWidget(self.playLastDuration, row, 3)

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
        self.bPop.setIcon(Icons.POPMENU)
        self.bPop.clicked.connect(self.popMenu)
        bPanel.layout().addWidget(self.bPop)
        self.bPop.setVisible(False)

        self.menu = QMenu(self)
        self.menu.addAction("Exclude").triggered.connect(self.doExclude)
        self.menu.addAction("Remove").triggered.connect(self.doRemove)
        self.menu.addAction("Open Folder").triggered.connect(self.openFolder)
        self.menu.addAction("Copy Name").triggered.connect(self.copySheetName)

        layout.addWidget(bPanel, row, 4)

    def popMenu(self, event):
        pos = pyautogui.position()
        self.menu.exec(QPoint(int(pos.x), int(pos.y)))

    def doExclude(self):
        pass

    def doRemove(self):
        pass

    def openFolder(self):
        pass

    def copySheetName(self):
        pass

    def startGame(self):
        OLABackend.SBSGL.launchGame(self.session, OLAGui.APP)

    def openInVault(self):
        OLABackend.openInVault(fullpath=self.vaultPath, sheetName=self.sheet)

    def setVaultName(self):
        text, ok = QInputDialog.getText(self, "Obsidian sheet name",
                                        "name:", QLineEdit.Normal,
                                        self.sheet)
        if ok and text:
            self.session.getGameInfo()['sheet'] = text
        OLABackend.SBSGL.procmgr.storage.save()

    def setSession(self, session, sheetAlreadySet=None):
        """
        :param: session: sbsbl.data.session
        """
        self.session = session
        sessionSheet = session.getGameInfo()['sheet']
        if sheetAlreadySet:
            if self.sheet != sessionSheet:
                self.session.getGameInfo()['sheet'] = self.sheet
                OLABackend.SBSGL.procmgr.storage.save()
        elif len(sessionSheet) > 0:
            self.sheet = sessionSheet
            self.name.setText(self.sheet)
            if OLABackend.VAULT_READY:
                self.sheetFile = OLABackend.VAULT.SHEETS[self.sheet]
        else:
            self.sheet = None
            self.name.setText(session.getName())
        self.applyPlatform()
        self.playDuration.setText(FormatUtil.formatDuration(session.getGameInfo()['duration']))
        self.playLastDuration.setText(FormatUtil.formatDuration(session.getGameInfo()['last_duration']))
        self.bVault.setVisible(True)
        self.bPop.setVisible(True)
        self.bVault.setEnabled(self.sheet is not None and len(self.sheet) > 0)
        self.bStart.setVisible(True)
        self.bStart.setEnabled(True)
        if self.linkVault:
            self.bLink.setVisible(False)

    def applyPlatform(self):
        icon = Icons.QUESTION
        if self.sheetFile is not None:
            size = len(self.sheetFile.platforms)
            if size == 1:
                icon = Icons.loadIcons(self.sheetFile.platforms[0])
            elif size > 1:
                icon = Icons.MANY
        self.platform.setPixmap(icon)

    def setPlaying(self, play):
        """
        :param play: MhMarkdownFile
        """
        self.vaultPath = str(play.path).replace(" ", "%20").replace("\\", "%2F")
        self.name.setText(play.name)
        self.sheetFile = play
        self.sheet = play.name
        session = OLABackend.SBSGL.procmgr.findSessionBySheetName(play.name)
        if session is None:
            self.bVault.setVisible(True)
            self.bStart.setVisible(True)
            self.bStart.setEnabled(False)
            self.bPop.setVisible(True)
            self.applyPlatform()
        else:
            self.setSession(session, sheetAlreadySet=True)

    def reset(self):
        self.sheetFile = None
        self.sheet = None
        self.session = None
        self.vaultPath = None
        self.platform.setPixmap(Icons.VOID)
        self.name.setText("")
        self.playDuration.setText("")
        self.playLastDuration.setText("")
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

        layout.addWidget(QLabel(), 0, 0)
        self.col1 = QLabel()
        self.col1.setMinimumWidth(300)
        if title is None:
            self.col1.setText("Game")
        else:
            self.col1.setText(title)
        self.col1.setStyleSheet(OLAGuiSetup.STYLE_QLABEL_TITLE)
        layout.addWidget(self.col1, 0, 1)
        layout.addWidget(QLabel("Total play time"), 0, 2)
        layout.addWidget(QLabel("Last play duration"), 0, 3)

        self.lines = []
        for idx in range(0, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.lines.append([])
            self.lines[idx].append(OLAGameLine(idx + 1, layout, linkVault=linkVault))

    def sessionMatchFilter(self, session):
        if OLAGui.FILTER.type is not None:
            if session.getSheet() is None:
                return True
            else:
                try:
                    return self.sheetMatchFilter(OLABackend.VAULT.SHEETS[session.getSheet()])
                except KeyError:
                    return True
        else:
            return True

    def sheetMatchFilter(self, sheet):
        if OLAGui.FILTER.type is None:
            return True
        for t in sheet.types:
            if t.startswith(OLAGui.FILTER.type):
                return True
        return False


class OLAGameSessions(OLASharedGameListWidget):
    def __init__(self):
        super().__init__(title="loading...", linkVault=True)
        OLAGui.SESSIONS = self

    def loadSessions(self):
        sessions = OLABackend.SBSGL.procmgr.getSessions()
        count = len(sessions)
        self.col1.setText("Game ( {} sessions )".format(count))
        current = 0
        if count > 0:
            logging.debug("OLAGameSessions:  Loading {} sessions :".format(count))
            for session in sessions:
                if self.sessionMatchFilter(session):
                    if current < OLAGuiSetup.VISIBLE_SESSION_COUNT:
                        self.lines[current][0].setSession(session)
                        current = current + 1
        else:
            logging.debug("OLAGameSessions: no session to load")

        for idx in range(current, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.lines[idx][0].reset()

    def reset(self):
        for idx in range(0, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.lines[idx][0].reset()


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
                sheet = OLABackend.VAULT.PLAY[play]
                if self.sheetMatchFilter(sheet):
                    if current < OLAGuiSetup.VISIBLE_SESSION_COUNT:
                        self.lines[current][0].setPlaying(sheet)
                        current = current + 1
        else:
            logging.debug("OLAGameSessions: no playing session to load")

        for idx in range(current, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.lines[idx][0].reset()

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

        OLABackend.SBSGL = SBSGL()
        self.startProcessCheck()
        OLAGui.ASSISTANT.vaultParsed()
        OLAGui.PLAYING_PANEL.refreshVault()
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
        OLAGui.PLAYING_PANEL.refreshSBSGL()
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
        OLAGui.SESSIONS.loadSessions()
        OLAGui.PLAYING_PANEL.refreshVault()

    def mdReportsGenerated(self):
        self.main.setStatus("Vault reports Generated")
        OLAGui.ASSISTANT.vaultParsed()

    def fileUsageGenerated(self):
        self.main.setStatus("File usage Generated")


logging.info("OLAApplication - starting application execution")
app = OLAApplication(sys.argv, OLAVersionInfo.VERSION)
# Blocking parsing of vault or display will be wrong
mdgen = MdReportGenerator(report=False)
mdgen.run()
app.start()
logging.info("OLAApplication - application terminated")
