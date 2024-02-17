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
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QSize, QThreadPool, QTimer, Qt
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QLabel, QMainWindow, \
    QVBoxLayout, \
    QApplication, QStatusBar, QToolBar, QGroupBox, QLineEdit, QGridLayout, QPushButton, QInputDialog, QComboBox, QMenu, QMessageBox, QCheckBox, QScrollBar, QScrollArea, QSplashScreen, QTextBrowser, QDialog

from base.fileutil import GhFileUtil
from base.formatutil import FormatUtil
from resources.resources import Icons
from sbsgl.sbsgl import SBSGL
from sbsgl.tools import MdReportGenerator, FileUsageGenerator, SgSGLProcessScanner, OLABackend


class OLAVersionInfo:
    VERSION = "2024.02.17a"
    PREVIOUS = "2024.02.11c"


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
    POSX = 350
    POSY = 1440
    PROCESS_SCANNER_TIMER = 20 * 1000
    GAME_NAME_MIN_WIDTH = 200
    TAG_MIN_WIDTH = 60
    VISIBLE_SESSION_COUNT = 20
    PAGE_VISIBLE_COUNT = 5
    PAGE_COUNT_WIDTH = 40
    PAGE_BUTTON_SIZE = 20
    VISIBLE_TYPE_COUNT = 15
    STYLE_QLABEL_TITLE = "QLabel{ border-width: 1px; border-style: dotted; border-color: darkblue; font-weight: bold;}"
    POSSIBLE_FILTER = ["#TYPE", "#PLAY"]
    DEFAULT_SESSION_FILTER = "INPROGRESS"
    DEFAULT_INSTALL_MODE_FILTER = True
    LINE_REPORTS_COUNT = 18


class OLAGui:
    APP = None
    MAIN = None
    TAB_PANEL = None
    PLAYING_PANEL = None
    SESSIONS = None
    REPORTS = None
    SESSIONS_TAB_NAME = "Sessions"
    ASSISTANT = None
    ASSISTANT_TAB_NAME = "Obsidian Sheets"
    EXCLUDED_TAB_NAME = "Excluded launchers"
    REPORTS_TAB_NAME = "Reports"

    @staticmethod
    def createContainerPanel(layout):
        pane = QWidget()
        pane.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)
        return pane

    @staticmethod
    def createToolbarButton(label, tip, icon, action):
        button = QPushButton(label)
        button.setStatusTip(tip)
        button.setIcon(icon)
        button.setIconSize(QSize(24,24))
        button.clicked.connect(action)
        return button


class OlaAbout(QDialog):
    def __init__(self, vault):
        super().__init__()
        about = """
            <!DOCTYPE html>
            <html>
            <body>
            <h1>OLA Obsidian Launcher Assistant</h1>
            <hr>
            Associated obsidian vault: <b>{}</b>
            <hr>
            Not related to obsidian project <a href="https://obsidian.md/">https://obsidian.md/</a> but highly recommended to use it.
            <br><br>
            <i>Third party software:
            <br>- Icon8 resources (https://icons8exit.com/icons)
            <br>- psutil pip module
            <br>- PySide pip module
            <br> Based on python</i>
            <br>
            <br>Copyright 2024 @ joetjo <a href="https://github.com/joetjo/OLA">https://github.com/joetjo/OLA</a>
            <br>Provided "as is" under Apache-2.0 License and to be used on your own responsibilities
            </body>
            </html>
            """.format(vault)
        self.content = QTextBrowser()
        self.content.setEnabled(False)
        self.content.setText(about)
        self.setWindowTitle("OLA {}".format(OLAVersionInfo.VERSION))
        self.setWindowIcon(Icons.HOME)
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.content)


class OLAToolbar(QWidget):
    def __init__(self, name):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        leftPane = OLAGui.createContainerPanel(QHBoxLayout())
        leftPane.layout().addWidget(OLAGui.createToolbarButton("", "Scan now to detect game process running",
                                                               Icons.REFRESH, OLAGui.APP.startProcessCheck))
        leftPane.layout().addWidget(OLAGui.createToolbarButton("", "Generate Markdown report and file usage",
                                                               Icons.REPORT, OLAGui.APP.startReporting))
        leftPane.layout().addWidget(OLAGui.createToolbarButton("", "Parse content of Obsidian vault",
                                                               Icons.IMPORT, OLAGui.APP.parseVault))
        layout.addWidget(leftPane)

        layout.addStretch()

        rightPane = OLAGui.createContainerPanel(QHBoxLayout())
        rightPane.layout().addWidget(OLAGui.createToolbarButton("","Maybe display some stiff about this wonderful application",
                                                                Icons.ABOUT,OLAGui.APP.showAbout))
        rightPane.layout().addWidget(OLAGui.createToolbarButton("","Don't know, maybe, stop the App",
                                                                Icons.EXIT,OLAGui.APP.shutdown))
        layout.addWidget(rightPane)


class OLAStatusBar(QStatusBar):

    def __init__(self):
        super().__init__()

    def set(self, message):
        self.showMessage("{} | {}".format(datetime.now().strftime("%H:%M:%S"), message))


class OLAFilter(QGroupBox):
    def __init__(self, tag, listener, defaultValue=None, defaultInstallMode=False, linkListener=None):
        super().__init__()
        self.tag = tag
        self.value = defaultValue
        self.filterValue = None

        self.searchToken = None

        layout = QGridLayout()
        self.setLayout(layout)

        if tag is not None:
            self.filterValue = QComboBox()
            self.filterValue.setMaxVisibleItems(OLAGuiSetup.VISIBLE_TYPE_COUNT)
            self.filterValue.currentTextChanged.connect(listener)
            self.filterValue.setCurrentText(self.value)
            tagLabel = QLabel("{}".format(self.tag))
            tagLabel.setMinimumWidth(OLAGuiSetup.TAG_MIN_WIDTH)
            layout.addWidget(tagLabel, 0, 0)
            layout.addWidget(QLabel(":"), 0, 1)
            layout.addWidget(self.filterValue, 0, 2)

        if linkListener is not None:
            linkLabel = QLabel()
            linkLabel.setPixmap(Icons.QUESTION)
            layout.addWidget(linkLabel, 0, 3)
            self.linkSelector = QCheckBox()
            self.linkSelector.stateChanged.connect(linkListener)
            layout.addWidget(self.linkSelector, 0, 4)

        if listener is not None:
            layout.addWidget(QLabel("Search"), 1, 0)
            layout.addWidget(QLabel(":"), 1, 1)
            self.search = QLineEdit()
            self.search.setMinimumWidth(10)
            self.search.editingFinished.connect(listener)
            layout.addWidget(self.search, 1, 2)

        if linkListener is not None:
            installLabel = QLabel()
            installLabel.setPixmap(Icons.PLAY)
            layout.addWidget(installLabel, 1, 3)
            self.installSelector = QCheckBox()
            if defaultInstallMode:
                self.installSelector.setCheckState(Qt.CheckState.Checked)
            self.installSelector.stateChanged.connect(linkListener)
            layout.addWidget(self.installSelector, 1, 4)

    def isFiltering(self):
        return self.value is not None or self.searchToken is not None

    def onLoad(self):
        self.value = self.filterValue.currentText()
        if len(self.value) == 0:
            self.value = None
        self.searchToken = self.search.text()
        if len(self.searchToken) == 0:
            self.searchToken = None

    def setValues(self):
        if self.tag is not None:
            if self.tag == OLAGuiSetup.POSSIBLE_FILTER[0]:
                choices = OLABackend.VAULT.TYPE_TAGS
            elif self.tag == OLAGuiSetup.POSSIBLE_FILTER[1]:
                choices = OLABackend.VAULT.PLAY_TAGS
            else:
                choices = ["{} not supported".format(self.tag)]
            currentValue = self.value
            self.filterValue.clear()
            self.filterValue.addItem("")
            self.filterValue.addItems(choices)
            self.filterValue.setCurrentText(currentValue)
            count = len(choices) + 1
            if count > OLAGuiSetup.VISIBLE_TYPE_COUNT:
                count = OLAGuiSetup.VISIBLE_TYPE_COUNT
            self.filterValue.setMaxVisibleItems(count)


class OLAPlayingPanel(QWidget):
    def __init__(self):
        super().__init__()

        OLAGui.PLAYING_PANEL = self

        self.sheet = None
        self.session = None
        self.rawName = None
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 5, 0)

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
        self.game.setMaximumWidth(OLAGuiSetup.GAME_NAME_MIN_WIDTH)
        self.game.setFixedWidth(OLAGuiSetup.GAME_NAME_MIN_WIDTH)
        leftPanelLayout.addWidget(self.game, 0, 3)
        self.bVault = QPushButton("")
        self.bVault.setStatusTip("Open in obsidian Vault")
        self.bVault.setIcon(Icons.OBSIDIAN)
        self.bVault.clicked.connect(self.openInVault)
        self.bVault.setVisible(False)
        leftPanelLayout.addWidget(self.bVault, 0, 4)

        self.bLink = QPushButton("")
        self.bLink.setStatusTip("Name in obsidian Vault")
        self.bLink.setIcon(Icons.PENCIL)
        self.bLink.clicked.connect(self.setVaultName)
        self.bLink.setVisible(False)
        leftPanelLayout.addWidget(self.bLink, 0, 5)

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

        # Search and filtering
        self.defaultFilter = OLAFilter(None, None)
        self.filters = dict()
        self.filters[OLAGui.SESSIONS_TAB_NAME] = OLAFilter(OLAGuiSetup.POSSIBLE_FILTER[1], self.applyFilter, defaultValue=OLAGuiSetup.DEFAULT_SESSION_FILTER, defaultInstallMode=OLAGuiSetup.DEFAULT_INSTALL_MODE_FILTER,
                                                           linkListener=self.applyCheck)
        self.filters[OLAGui.ASSISTANT_TAB_NAME] = OLAFilter(OLAGuiSetup.POSSIBLE_FILTER[0], self.applyFilter)
        self.filter = self.defaultFilter

        self.layout().addWidget(self.defaultFilter)
        self.layout().addWidget(self.filters[OLAGui.SESSIONS_TAB_NAME])
        self.filters[OLAGui.SESSIONS_TAB_NAME].setVisible(False)
        self.layout().addWidget(self.filters[OLAGui.ASSISTANT_TAB_NAME])
        self.filters[OLAGui.ASSISTANT_TAB_NAME].setVisible(False)

    def activateFilter(self, tabName):
        selectedFilter = None
        for k, f in self.filters.items():
            if k == tabName:
                selectedFilter = f
            else:
                f.setVisible(False)
        if selectedFilter is None:
            selectedFilter = self.defaultFilter
        else:
            self.defaultFilter.setVisible(False)
        selectedFilter.setVisible(True)
        self.filter = selectedFilter

    def applyFilter(self):
        if self.filter.filterValue is not None:  # When reloading values after parsing Vault
            self.filter.value = self.filter.filterValue.currentText()
            if len(self.filter.value) == 0:
                self.filter.value = None
        else:
            self.filter.value = None
        OLAGui.ASSISTANT.vaultParsed()
        OLAGui.SESSIONS.loadSessions()

    def applyCheck(self):
        OLAGui.SESSIONS.showUnlink = self.filters[OLAGui.SESSIONS_TAB_NAME].linkSelector.isChecked()
        OLAGui.SESSIONS.showOnlyInstalled = self.filters[OLAGui.SESSIONS_TAB_NAME].installSelector.isChecked()
        OLAGui.SESSIONS.loadSessions()

    def refreshVault(self):
        for k, f in self.filters.items():
            f.setValues()

    def refreshSBSGL(self, force=False):
        game = OLABackend.SBSGL.procmgr.getCurrentGame()
        if game is not None:
            if game.getName() != self.rawName or force:
                self.rawName = game.getName()
                self.session = game.process.getStoreEntry()
                self.sheet = self.session["sheet"]
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
                self.bLink.setVisible(True)
        elif self.game.text() != "":
            self.gameIcon.setPixmap(Icons.VOID)
            self.game.setText("")
            self.ptimeIcon.setPixmap(Icons.VOID)
            self.ptime.setText("")
            self.bVault.setVisible(False)
            self.bLink.setVisible(False)
            self.session = None
            self.sheet = None

    def gameLaunchFailure(self):
        self.game.setText("Game not available")
        self.gameIcon.setPixmap(Icons.KO)

    def openInVault(self):
        OLABackend.openInVault(sheetName=self.sheet)

    def setVaultName(self):
        OLAGameLine.requestVaultNameDialog(self.session, self.sheet, GhFileUtil.ConvertUpperCaseWordSeparatedNameToStr(self.game.text()), self)


class OLAGameLine(QWidget):
    def __init__(self, row, layout, sessionMode=False):
        super().__init__()

        self.vaultPath = None
        self.session = None
        self.sheet = None
        self.sheetFile = None
        self.sessionMode = sessionMode

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

        if sessionMode:
            self.bLink = QPushButton("")
            self.bLink.setStatusTip("Name in obsidian Vault")
            self.bLink.setIcon(Icons.PENCIL)
            self.bLink.clicked.connect(self.setVaultName)
            bPanel.layout().addWidget(self.bLink)
            self.bLink.setVisible(False)

        self.bVault = QPushButton("")
        self.bVault.setStatusTip("Open in obsidian Vault")
        self.bVault.setIcon(Icons.OBSIDIAN)
        self.bVault.clicked.connect(self.openInVault)
        bPanel.layout().addWidget(self.bVault)
        self.bVault.setVisible(False)

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

        layout.addWidget(bPanel, row, 4)

        self.menu = QMenu(self)
        if sessionMode:
            self.menu.addAction("Setup Launcher").triggered.connect(self.doSetupLauncher)
            self.menu.addAction("Exclude").triggered.connect(self.doExclude)
            self.menu.addAction("Remove").triggered.connect(self.doRemove)
            self.menu.addAction("Open Folder").triggered.connect(self.openFolder)
            self.menu.addAction("Copy Name").triggered.connect(self.copyPathName)
        else:
            self.menu.addAction("Copy Name").triggered.connect(self.copySheetName)

    def popMenu(self):
        self.menu.exec(QCursor.pos())

    def doExclude(self):
        msgBox = QMessageBox()
        msgBox.setText("Confirm Exclusion")
        msgBox.setInformativeText("Game data will be deleted and it could be restored through the excluded game tab?")
        msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Cancel)
        ret = msgBox.exec_()
        if ret == QMessageBox.Save:
            OLABackend.SBSGL.procmgr.ignore(self.session.getName())
            OLAGui.TAB_PANEL.reload()

    def doRemove(self):
        msgBox = QMessageBox()
        msgBox.setText("Confirm Removal")
        msgBox.setInformativeText("Game data will be deleted, no possible rollback?")
        msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Cancel)
        ret = msgBox.exec_()
        if ret == QMessageBox.Save:
            OLABackend.SBSGL.procmgr.remove(self.session.getName())
            OLAGui.TAB_PANEL.reload()

    def openFolder(self):
        if self.session is not None:
            logging.info("Open explorer on {}".format(self.session.getPath()))
            subprocess.Popen("explorer /select, \"{}\"".format(self.session.getPath()))

    def copySheetName(self):
        QApplication.clipboard().setText(self.sheet)

    def copyPathName(self):
        QApplication.clipboard().setText(self.name.text())

    def startGame(self):
        if self.sheet is not None and len(self.sheet) > 0:
            self.openInVault()
        OLABackend.SBSGL.launchGame(self.session, OLAGui.APP)

    def openInVault(self):
        OLABackend.openInVault(fullpath=self.vaultPath, sheetName=self.sheet)

    def doSetupLauncher(self):
        pass

    @staticmethod
    def requestVaultNameDialog(sessionInfo, sheet, defaultValue, parent):
        val = sheet
        if val is None or len(val) == 0:
            val = defaultValue
        text, ok = QInputDialog.getText(parent, "Obsidian sheet name",
                                        "name:", QLineEdit.Normal,
                                        val)
        if ok and text:
            sessionInfo['sheet'] = text
        OLABackend.SBSGL.procmgr.storage.save()
        OLAGui.TAB_PANEL.reload()
        OLAGui.PLAYING_PANEL.refreshSBSGL(force=True)

    def setVaultName(self):
        OLAGameLine.requestVaultNameDialog(self.session.getGameInfo(), self.sheet, GhFileUtil.ConvertUpperCaseWordSeparatedNameToStr(self.name.text()), self)

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
                try:
                    self.sheetFile = OLABackend.VAULT.SHEETS[self.sheet]
                except KeyError:
                    self.sheetFile = None
        else:
            self.sheet = None
            self.sheetFile = None
            self.name.setText(session.getName())
        self.applyPlatform()
        self.playDuration.setText(FormatUtil.formatDuration(session.getGameInfo()['duration']))
        self.playLastDuration.setText(FormatUtil.formatDuration(session.getGameInfo()['last_duration']))
        self.bVault.setVisible(True)
        self.bPop.setVisible(True)
        self.bVault.setEnabled(self.sheet is not None and len(self.sheet) > 0)
        self.bStart.setVisible(True)
        self.bStart.setEnabled(session.installed)
        if self.sessionMode:
            self.bLink.setVisible(True)

    def applyPlatform(self):
        icon = Icons.NOT_FOUND
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
        if self.sessionMode:
            self.bLink.setVisible(False)


class OLASharedGameListWidget(QWidget):
    def __init__(self, name, title=None, sessionMode=False):
        super().__init__()
        self.name = name
        self.currentPage = 1
        self.currentPageCount = 1
        self.showUnlink = False
        self.showOnlyInstalled = OLAGuiSetup.DEFAULT_INSTALL_MODE_FILTER

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

        #
        # PAGINATION
        #
        pagePanel = QWidget()
        pagePanelLayout = QHBoxLayout()
        pagePanelLayout.setContentsMargins(0, 0, 0, 0)
        pagePanelLayout.addStretch()
        pagePanel.setLayout(pagePanelLayout)

        self.bBack = QPushButton("<")
        self.bBack.setMaximumWidth(OLAGuiSetup.PAGE_BUTTON_SIZE)
        pagePanelLayout.addWidget(self.bBack)
        self.bBack.clicked.connect(self.doBack)
        self.bBack.setEnabled(False)

        self.page = QComboBox()
        self.page.setMaxVisibleItems(OLAGuiSetup.PAGE_VISIBLE_COUNT)
        self.page.currentTextChanged.connect(self.pageSelected)
        self.page.addItems("1")
        self.page.setEditable(True)
        self.page.setCurrentText("1")
        pagePanelLayout.addWidget(self.page)
        self.page.setMinimumWidth(OLAGuiSetup.PAGE_COUNT_WIDTH)

        self.pageCount = QLabel("")
        pagePanelLayout.addWidget(self.pageCount)

        self.bFront = QPushButton(">")
        self.bFront.setMaximumWidth(OLAGuiSetup.PAGE_BUTTON_SIZE)
        pagePanelLayout.addWidget(self.bFront)
        self.bFront.clicked.connect(self.doFront)
        self.bFront.setEnabled(False)

        layout.addWidget(pagePanel, 0, 4)

        #
        # LINES
        #
        self.lines = []
        for idx in range(0, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.lines.append([])
            self.lines[idx].append(OLAGameLine(idx + 1, layout, sessionMode=sessionMode))
        self.filter = self.filter = OLAGui.PLAYING_PANEL.filters[name]

    def sessionMatchFilter(self, session):
        sheetUnset = len(session.getSheet()) == 0
        if not self.showUnlink and sheetUnset:
            return False
        if self.showOnlyInstalled and not session.installed:
            return False
        if self.filter.searchToken is not None and not self.filter.searchToken in session.getName():
            return False
        if self.filter.value is not None:
            if sheetUnset:
                return True
            else:
                try:
                    return self.sheetMatchFilter(OLABackend.VAULT.SHEETS[session.getSheet()])
                except KeyError:
                    return True
        # else: Filter.value is None / No Active Search
        elif self.showUnlink and not sheetUnset:  # Ack to show only unlink session when show unlink selected and no filtering
            return False
        else:
            return True

    def sheetMatchFilter(self, sheet):
        if self.filter.searchToken is not None and not self.filter.searchToken in sheet.name:
            return False
        if self.filter.value is None:
            return True
        if self.filter.tag == OLAGuiSetup.POSSIBLE_FILTER[0]:
            tags = sheet.type_tags
        elif self.filter.tag == OLAGuiSetup.POSSIBLE_FILTER[1]:
            tags = sheet.play_tags
        else:
            return True
        for t in tags:
            if t.startswith(self.filter.value):
                return True
        return False

    def doBack(self):
        if self.currentPage > 1:
            self.currentPage = self.currentPage - 1
        self.reload()

    def doFront(self):
        if self.currentPage < self.currentPageCount:
            self.currentPage = self.currentPage + 1
        self.reload()

    def pageSelected(self):
        try:
            requested = int(self.page.currentText())
            if 1 < requested < self.currentPageCount and requested != self.currentPage:
                self.currentPage = requested
                self.reload()
        except ValueError:
            self.page.setCurrentText(str(self.currentPage))

    def setPageCount(self, count):
        currentCount = self.currentPageCount
        self.currentPageCount = int(count / OLAGuiSetup.VISIBLE_SESSION_COUNT)
        if self.currentPageCount != count / OLAGuiSetup.VISIBLE_SESSION_COUNT:
            self.currentPageCount = self.currentPageCount + 1
        self.pageCount.setText("/{}".format(self.currentPageCount))
        if self.currentPageCount != currentCount:
            self.page.clear()
            for page in range(1, self.currentPageCount + 1):
                self.page.addItem(str(page))
        self.page.setCurrentText(str(self.currentPage))
        self.bBack.setEnabled(self.currentPage > 1)
        self.bFront.setEnabled(self.currentPage < self.currentPageCount)

    def reload(self):
        pass  # To be overridden

    def loadTitle(self, count):
        pass  # To be overridden

    def matchFilter(self, data):
        pass  # To be overridden

    def setData(self, gameLine, data):
        pass  # To be overridden

    def load(self, rawList):
        self.filter.onLoad()
        if self.showUnlink or self.showOnlyInstalled or self.filter.isFiltering():
            selList = []
            for data in rawList:
                if self.matchFilter(data):
                    selList.append(data)
        else:
            selList = rawList
        count = len(selList)
        self.setPageCount(count)
        self.col1.setText(self.loadTitle(count))

        checkedCount = 0
        checkedCountToStart = (self.currentPage - 1) * OLAGuiSetup.VISIBLE_SESSION_COUNT
        currentDisplayed = 0
        if count > 0:
            for data in selList:
                checkedCount = checkedCount + 1
                if checkedCount > checkedCountToStart and currentDisplayed < OLAGuiSetup.VISIBLE_SESSION_COUNT:
                    self.setData(self.lines[currentDisplayed][0], data)
                    currentDisplayed = currentDisplayed + 1

        for idx in range(currentDisplayed, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.lines[idx][0].reset()

    def reset(self):
        for idx in range(0, OLAGuiSetup.VISIBLE_SESSION_COUNT):
            self.lines[idx][0].reset()


class OLAGameSessions(OLASharedGameListWidget):
    def __init__(self, ):
        super().__init__(OLAGui.SESSIONS_TAB_NAME, title="loading...", sessionMode=True)
        OLAGui.SESSIONS = self

    def loadSessions(self):
        self.load(OLABackend.SBSGL.procmgr.getSessions())

    def loadTitle(self, count):
        return "Game ( {} sessions )".format(count)

    def matchFilter(self, data):
        return self.sessionMatchFilter(data)

    def setData(self, gameLine, data):
        gameLine.setSession(data)

    def reload(self):
        self.loadSessions()


class OLAReportLine(QWidget):
    def __init__(self, row, col, layout, sheetPath, about, customLabel=None):
        super().__init__()

        self.sheet = sheetPath

        if col == 2:
            layout.addWidget(QLabel(" | "), row, 2)
            colUpdated = 3
        else:
            colUpdated = col

        if customLabel is None:
            sname = os.path.basename(sheetPath)
            sname = sname[0:len(sname) - 3]
            sheet = QLabel(sname)
        else:
            sheet = QLabel(customLabel)
        sheet.setToolTip(about)
        layout.addWidget(sheet, row, colUpdated)

        bPanel = QWidget()
        bPanel.setLayout(QHBoxLayout())
        bPanel.layout().setContentsMargins(0, 0, 0, 0)

        bVault = QPushButton("")
        bVault.setStatusTip("Open in obsidian Vault")
        bVault.setIcon(Icons.OBSIDIAN)
        bVault.clicked.connect(self.openReportInVault)
        bVault.setEnabled(False)
        bPanel.layout().addWidget(bVault)
        self.bVault = bVault

        if customLabel is None:
            bRedo = QPushButton("")
            bRedo.setStatusTip("Regenerate only this report")
            bRedo.setIcon(Icons.REPORT)
            bRedo.clicked.connect(self.startSingleReport)
            bRedo.setEnabled(False)
            bPanel.layout().addWidget(bRedo)
            self.bRedo = bRedo
        else:
            self.bRedo = None

        bPanel.layout().addStretch()

        layout.addWidget(bPanel, row, colUpdated + 1)

    def openReportInVault(self):
        OLABackend.openInVault(sheetName=self.sheet)

    def startSingleReport(self):
        OLAGui.APP.startSingleReport(self.sheet)

    def enableVault(self):
        self.bVault.setEnabled(True)
        if self.bRedo is not None:
            self.bRedo.setEnabled(True)

    def regenerateReport(self):
        OLAGui.APP.startSingleReport(self.sheet)


class OLAReports(QWidget):
    def __init__(self):
        super().__init__()
        OLAGui.REPORTS = self
        self.reports = dict()
        self.start = time.time()

        layout = QVBoxLayout()
        self.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(OLAGuiSetup.VISIBLE_SESSION_COUNT)
        content = QWidget()
        content.setLayout(QHBoxLayout())
        reportPanel = QWidget()
        self.reportPanelLayout = QGridLayout()
        reportPanel.setLayout(self.reportPanelLayout)
        content.layout().addWidget(reportPanel)
        content.layout().addStretch()
        scroll.setWidget(content)

        layout.addWidget(scroll)

        statusLine = QWidget()
        statusLine.setLayout(QHBoxLayout())
        statusLine.setContentsMargins(0, 0, 0, 0)
        self.reportStatus = QLabel("Starting report generation")
        statusLine.layout().addWidget(self.reportStatus)
        statusLine.layout().addStretch()
        self.linkErrorMessage = QLabel("")
        statusLine.layout().addWidget(self.linkErrorMessage)
        layout.addWidget(statusLine)

    def reportAvailable(self, sheetPath):
        self.setStatus("{} generated".format(sheetPath))
        self.reports[sheetPath].enableVault()

    def setStatus(self, message):
        elapsed = str(round(time.time() - self.start, 1))
        self.reportStatus.setText("{}s | {}".format(elapsed, message))

    def setLinkCheckStatus(self, message, detailed=None):
        self.linkErrorMessage.setText(message)
        if detailed is None:
            self.linkErrorMessage.setToolTip("")
        else:
            self.linkErrorMessage.setToolTip("\n".join(detailed))

    def setReports(self, sheetPaths):
        self.reports["Readme"] = OLAReportLine(0, 0, self.reportPanelLayout, OLABackend.VAULT.REPORTS_SHEET_NAME, "All reports description", customLabel="Reports description")
        self.reports["Readme"].enableVault()
        row = 0
        col = 2
        for sheetPath, about in sheetPaths.items():
            self.reports[sheetPath] = OLAReportLine(row, col, self.reportPanelLayout, sheetPath, about)
            if col == 0:
                col = 2
            elif col == 2:
                col = 5
            else:
                row = row + 1
                col = 0
        self.reports["Duplicate files"] = OLAReportLine(row, col, self.reportPanelLayout, OLABackend.VAULT.REPORTS_DUPFILE_NAME, "Report that identify duplicate files in predefined folders",
                                                        customLabel="Files duplication")
        self.reports["Duplicate files"].enableVault()

        for idx in range(row, OLAGuiSetup.LINE_REPORTS_COUNT):
            self.reportPanelLayout.addWidget(QLabel(""), idx, 0)


class OLAObsidianAssistant(OLASharedGameListWidget):
    def __init__(self):
        super().__init__(OLAGui.ASSISTANT_TAB_NAME, title="Obsidian vault not parsed")
        OLAGui.ASSISTANT = self
        self.title = "Obsidian files not parsed"

    def loadPlaying(self):
        self.load(sorted(OLABackend.VAULT.PLAY, key=lambda x: x.lastModif, reverse=True))

    def loadTitle(self, count):
        return "{}, {} displayed)".format(self.title, count)

    def matchFilter(self, data):
        return self.sheetMatchFilter(data)

    def setData(self, gameLine, data):
        gameLine.setPlaying(data)

    def reload(self):
        self.loadPlaying()

    def vaultReportInProgress(self):
        self.title = "Vault report generation in progress"
        self.col1.setText(self.title)

    def vaultParsingInProgress(self):
        self.title = "Vault loading in progress"
        self.col1.setText(self.title)

    def vaultParsed(self):
        self.title = "Vault: {} files, {} tags".format(len(OLABackend.VAULT.SORTED_FILES), len(OLABackend.VAULT.TAGS))
        self.col1.setText(self.title)
        self.loadPlaying()
        if OLAGui.REPORTS is not None:
            OLAGui.REPORTS.setStatus("Reports generation finished")


class OLAExcludedGame(QWidget):
    def __init__(self):
        super().__init__()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("NOT AVAILABLE - EDIT THE STORAGE ON YOUR OWN !!!"))
        self.layout().addStretch()


class OLATabPanel(QTabWidget):

    def __init__(self):
        super().__init__()
        OLAGui.TAB_PANEL = self

        self.setTabPosition(QTabWidget.North)
        self.setMovable(False)

        self.tabs = dict()
        self.tabsIndex = dict()
        self.tabsName = []
        self.declareTab(OLAGameSessions(), OLAGui.SESSIONS_TAB_NAME)
        self.declareTab(OLAObsidianAssistant(), OLAGui.ASSISTANT_TAB_NAME)
        self.declareTab(OLAExcludedGame(), OLAGui.EXCLUDED_TAB_NAME)

        self.currentChanged.connect(self.tabSelected)

    def declareTab(self, widget, name):
        self.tabsIndex[name] = len(self.tabs)
        self.tabs[name] = widget
        self.tabsName.append(name)
        self.addTab(widget, name)

    def removeTabByName(self, name):
        try:
            self.removeTab(self.tabsIndex[name])
            del self.tabs[name]
            del self.tabsIndex[name]
            self.tabsName.remove(name)
        except KeyError:
            pass  # was not here

    def clearAndShowReportsTab(self):
        self.removeTabByName(OLAGui.REPORTS_TAB_NAME)
        self.declareTab(OLAReports(), OLAGui.REPORTS_TAB_NAME)
        self.setCurrentIndex(self.tabsIndex[OLAGui.REPORTS_TAB_NAME])

    def tabSelected(self):
        OLAGui.PLAYING_PANEL.activateFilter(self.tabsName[self.currentIndex()])

    def reload(self):
        OLAGui.SESSIONS.reload()
        OLAGui.ASSISTANT.reload()


class OLAMainWindow(QMainWindow):
    def __init__(self, version):
        super().__init__()
        OLAGui.MAIN = self
        self.setWindowTitle("Obsidian Launcher Assistant [SBSGL] - {}".format(version))

        self.move(OLAGuiSetup.POSX, OLAGuiSetup.POSY)

        self.status = OLAStatusBar()
        self.setStatusBar(self.status)
        self.status.set("Loading in progress...")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = OLAToolbar("Main toolbar")
        layout.addWidget(self.toolbar)

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

        self.splash = QSplashScreen(Icons.SPLASH)
        self.splash.show()
        self.processEvents()

        # Blocking parsing of vault or display will be wrong
        mdgen = MdReportGenerator(allReports=False)
        mdgen.run()
        self.splash.showMessage("{} - loading vault...".format(OLAVersionInfo.VERSION))
        self.processEvents()

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

    def showAbout(self):
        about = OlaAbout(OLABackend.VAULT.VAULT)
        about.show()
        about.exec()

    def start(self):
        OLAGui.TAB_PANEL.tabSelected()
        OLABackend.SBSGL = SBSGL()
        self.startProcessCheck()
        OLAGui.ASSISTANT.vaultParsed()
        OLAGui.PLAYING_PANEL.refreshVault()
        self.main.show()
        self.exec()

    def checkSplash(self):
        if self.splash is not None:
            self.splash.setVisible(False)
            self.splash = None

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
        mdgen = MdReportGenerator(allReports=False)
        mdgen.signals.md_report_generation_finished.connect(self.mdParsed)
        self.threadpool.start(mdgen)

    def startReporting(self):
        OLAGui.TAB_PANEL.clearAndShowReportsTab()
        OLAGui.ASSISTANT.vaultReportInProgress()
        mdgen = MdReportGenerator(allReports=True)
        mdgen.signals.md_report_generation_finished.connect(self.mdParsed)
        mdgen.signals.md_report_generation_starting.connect(self.mdStarting)
        mdgen.signals.md_last_report.connect(self.mdReportGenerated)
        self.threadpool.start(mdgen)

        filegen = FileUsageGenerator()
        filegen.signals.file_usage_generation_finished.connect(self.fileUsageGenerated)
        filegen.signals.sheet_link_progress.connect(self.sheetLinkProgress)
        filegen.signals.sheet_link_finished.connect(self.sheetLinkChecked)
        self.threadpool.start(filegen)

    def startSingleReport(self, target):
        mdgen = MdReportGenerator(target=target, allReports=False)
        mdgen.signals.md_report_generation_finished.connect(self.ignoreSignal)
        mdgen.signals.md_report_generation_starting.connect(self.ignoreSignal)
        mdgen.signals.md_last_report.connect(self.mdReportGenerated)
        self.threadpool.start(mdgen)

    def ignoreSignal(self):
        pass

    def scanFinished(self):
        self.checkSplash()
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

    def mdReportGenerated(self, reportName, sheet):
        OLAGui.REPORTS.reportAvailable(sheet)

    def mdParsed(self):
        self.checkSplash()
        self.main.setStatus("Vault parsed")
        OLAGui.ASSISTANT.vaultParsed()
        OLAGui.SESSIONS.loadSessions()
        OLAGui.PLAYING_PANEL.refreshVault()

    def mdStarting(self, reports):
        OLAGui.REPORTS.setReports(reports)

    def mdReportsGenerated(self):
        self.mdParsed()

    def fileUsageGenerated(self):
        self.main.setStatus("File usage Generated")

    def sheetLinkProgress(self, message):
        OLAGui.REPORTS.setLinkCheckStatus(message)

    def sheetLinkChecked(self, sessionCount, linkCount, brokenLinkCount, repairedLink, names):
        message = "{}/{} vault links".format(linkCount, sessionCount)
        if brokenLinkCount > 0:
            message = "{} | {} removed links".format(message, brokenLinkCount)
        if repairedLink > 0:
            message = "{} | {} inserted links".format(message, repairedLink)
        OLAGui.REPORTS.setLinkCheckStatus(message, names)


logging.info("OLAApplication - starting application execution")
app = OLAApplication(sys.argv, OLAVersionInfo.VERSION)
app.start()
logging.info("OLAApplication - application terminated")
