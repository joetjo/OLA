# Copyright 2025 joetjo https://github.com/joetjo/OLA
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
import time
from datetime import datetime

from PySide6 import QtGui
from PySide6.QtCore import QCoreApplication, QSize, QThreadPool, QTimer, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QLabel, QMainWindow, \
    QVBoxLayout, \
    QApplication, QStatusBar, QGroupBox, QLineEdit, QGridLayout, QPushButton, QInputDialog, QComboBox, QMenu, QMessageBox, QCheckBox, QScrollArea, QSplashScreen, QTextBrowser, QDialog, QFileDialog

from base.fileutil import GhFileUtil
from base.formatutil import FormatUtil
from base.setup import GhSetup
from resources.resources import Icons
from sbsgl.sbsgl import SBSGL
from sbsgl.tools import MdReportGenerator, FileUsageGenerator, SgSGLProcessScanner, OLABackend


class OLAVersionInfo:
    VERSION = "2025.03.23c"
    PREVIOUS = "2025.03.20"


class OLAGuiSetup:
    DEV_MODE = True
    # Constants - not (yet?) configurable
    PROCESS_SCANNER_TIMER = 20 * 1000
    GAME_NAME_MIN_WIDTH = 200
    TAG_MIN_WIDTH = 60
    VISIBLE_SESSION_COUNT = 20
    PAGE_VISIBLE_COUNT = 5
    PAGE_COUNT_WIDTH = 40
    PAGE_BUTTON_SIZE = 20
    VISIBLE_TYPE_COUNT = 15
    STYLE_QLABEL_TITLE = "QLabel{ border-width: 1px; border-style: dotted; border-color: darkblue; font-weight: bold;}"
    STYLE_QLABEL_EXTRAINFO = "QLabel{font: italic;color: gray;}"
    STYLE_QLABEL_COMMENT = "border-width: 1px; border-style: dotted; border-color: gray;"
    STYLE_QLINE_EDITABLE = "QLineEdit{border-width: 2px; border-style: outset; border-color: lightgray; font-weight: bold}"
    STYLE_QLINE_EDITED = "QLineEdit{border-width: 2px; border-style: outset; border-color: red; background-color: white; font-weight: bold}"
    SHEET_VIEW_FILTER_TAG = "#TYPE"
    SESSION_VIEW_FILTER_TAG = "#PLAY"
    REPORT_VIEW_FILTER_ID = "Group"
    DEFAULT_SESSION_FILTER = "INPROGRESS"
    DEFAULT_INSTALL_MODE_FILTER = True
    DEFAULT_VN_MODE_FILTER = True
    DEFAULT_VNA_MODE_FILTER = False
    # CONFIGURABLE ENTRIES
    POSX = "posx"
    POSY = "posy"
    HEIGHT = "height"
    WIDTH = "width"
    DEFAULT_GAME_FOLDER = "default game folder"

    @staticmethod
    def getSetupEntry(name):
        return OLAGui.APP.olaSetup.get(name)

    def __init__(self, print_mode, content=None):
        self.print_mode = print_mode
        self.setupFile = GhSetup('OLA', content)
        self.SETUP = self.setupFile.getBloc("OLA")
        self.dirty = False

        if print_mode:
            print("================= OLA SETUP  =========================")
        self.posx = self.initSetupEntry(OLAGuiSetup.POSX, 10)
        self.posy = self.initSetupEntry(OLAGuiSetup.POSY, 10)
        self.height = self.initSetupEntry(OLAGuiSetup.HEIGHT, 0)
        self.width = self.initSetupEntry(OLAGuiSetup.WIDTH, 0)
        self.default_game_folder = self.initSetupEntry(OLAGuiSetup.DEFAULT_GAME_FOLDER, "" )

    def initSetupEntry(self, name, default_value):
        reset = ""
        try:
            value = self.SETUP[name]
        except KeyError:
            self.SETUP[name] = default_value
            value = default_value
            self.dirty = True
        if self.print_mode:
            print(">>>>>>> {}: {}{}".format(name, value, reset))
        return value

    # set property value and generate KeyError is this is not a supported key entry
    # return previous value
    def set(self, name, value):
        old = self.SETUP[name]
        self.SETUP[name] = value
        if not self.dirty:
            print("Setup has been modified and has to be saved")
            self.dirty = True
        return old

    # get property value and generate KeyError is this is not a supported key entry
    def get(self, name):
        return self.SETUP[name]

    def save(self):
        self.setupFile.save()
        self.dirty = False

class OLALock:
    MDENGINE = False

    @staticmethod
    def takeMdEngine():
        if OLALock.MDENGINE:
            return False
        else:
            OLALock.MDENGINE = True
            return True

    @classmethod
    def releaseMDEngine(cls):
        OLALock.MDENGINE = False


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
        button.setIconSize(QSize(24, 24))
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
            <br>Copyright 2025 @ joetjo <a href="https://github.com/joetjo/OLA">https://github.com/joetjo/OLA</a>
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
    def __init__(self):
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
        rightPane.layout().addWidget(OLAGui.createToolbarButton("", "Maybe display some stiff about this wonderful application",
                                                                Icons.ABOUT, OLAGui.APP.showAbout))
        rightPane.layout().addWidget(OLAGui.createToolbarButton("", "Don't know, maybe, stop the App",
                                                                Icons.EXIT, OLAGui.APP.shutdown))
        layout.addWidget(rightPane)


class OLAStatusBar(QStatusBar):

    def __init__(self):
        super().__init__()

    def set(self, message):
        self.showMessage("{} | {}".format(datetime.now().strftime("%H:%M:%S"), message))


class OLAFilter(QGroupBox):
    def __init__(self, tag, listener, defaultValue=None, defaultInstallMode=False, linkListener=None, searchEnabled=True):
        super().__init__()
        self.tag = tag
        self.value = defaultValue
        self.filterValue = None
        self.textListener = listener
        self.searchToken = None

        layout = QGridLayout()
        self.setLayout(layout)

        if tag is not None:
            self.filterValue = QComboBox()
            self.filterValue.setMaxVisibleItems(OLAGuiSetup.VISIBLE_TYPE_COUNT)
            self.filterValue.setCurrentText(self.value)
            self.filterValue.currentTextChanged.connect(self.textListener)
            tagLabel = QLabel("{}".format(self.tag))
            tagLabel.setMinimumWidth(OLAGuiSetup.TAG_MIN_WIDTH)
            layout.addWidget(tagLabel, 0, 0)
            layout.addWidget(QLabel(":"), 0, 1)
            layout.addWidget(self.filterValue, 0, 2)

        if linkListener is not None:
            self.vnSelector = OLAFilter.createCheckbox(layout, 0, 3, linkListener,
                                                       Icons.STORY1,
                                                       "Display also Simple Story game (VN)",
                                                       default=OLAGuiSetup.DEFAULT_VN_MODE_FILTER)
            self.vnaSelector = OLAFilter.createCheckbox(layout, 0, 5, linkListener,
                                                        Icons.STORY2,
                                                        "Display also Adult Story game (VNA)",
                                                       default=OLAGuiSetup.DEFAULT_VNA_MODE_FILTER )

        if listener is not None:
            layout.addWidget(QLabel("Search"), 1, 0)
            layout.addWidget(QLabel(":"), 1, 1)
            self.search = QLineEdit()
            self.search.setMinimumWidth(10)
            self.search.setDisabled(not searchEnabled)
            self.search.setEnabled(searchEnabled)
            self.search.editingFinished.connect(listener)
            layout.addWidget(self.search, 1, 2)

        if linkListener is not None:
            self.linkSelector = OLAFilter.createCheckbox(layout, 1, 3,
                                                         linkListener, Icons.QUESTION, "Display also game not properly declared in Obsidian")
            self.installSelector = OLAFilter.createCheckbox(layout, 1, 5,
                                                            linkListener, Icons.PLAY, "Display only installed game", default = defaultInstallMode )

    @staticmethod
    def createCheckbox(layout, line, pos, listener, icon, tip, default = False ):
        linkLabel = QLabel()
        linkLabel.setPixmap(icon)
        linkLabel.setToolTip(tip)
        layout.addWidget(linkLabel, line, pos)
        result = QCheckBox()
        if default:
            result.setCheckState(Qt.CheckState.Checked)
        result.setToolTip(tip)
        result.stateChanged.connect(listener)
        layout.addWidget(result, line, pos+1)
        return result

    def isFiltering(self):
        return self.value is not None or self.searchToken is not None

    def onLoad(self):
        self.value = self.filterValue.currentText()
        if len(self.value) == 0:
            self.value = None
        self.searchToken = self.search.text()
        if len(self.searchToken) == 0:
            self.searchToken = None

    def setNoSelection(self):
        if self.textListener is not None:
            self.filterValue.currentTextChanged.disconnect(self.textListener)
        self.filterValue.setCurrentText(None)
        self.value = None
        if self.textListener is not None:
            self.filterValue.currentTextChanged.connect(self.textListener)

    def setValues(self):
        if self.textListener is not None:
            self.filterValue.currentTextChanged.disconnect(self.textListener)
        if self.tag is not None:
            if self.tag == OLAGuiSetup.SHEET_VIEW_FILTER_TAG:
                choices = OLABackend.VAULT.TYPE_TAGS
            elif self.tag == OLAGuiSetup.SESSION_VIEW_FILTER_TAG:
                choices = OLABackend.VAULT.PLAY_TAGS
            elif self.tag == OLAGuiSetup.REPORT_VIEW_FILTER_ID:
                choices = OLABackend.VAULT.REPORTS_GROUP
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
        if self.textListener is not None:
            self.filterValue.currentTextChanged.connect(self.textListener)


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
        self.filters[OLAGui.SESSIONS_TAB_NAME] = OLAFilter(OLAGuiSetup.SESSION_VIEW_FILTER_TAG,
                                                           self.applyFilter,
                                                           defaultValue=OLAGuiSetup.DEFAULT_SESSION_FILTER,
                                                           defaultInstallMode=OLAGuiSetup.DEFAULT_INSTALL_MODE_FILTER,
                                                           linkListener=self.applyCheck)
        self.filters[OLAGui.ASSISTANT_TAB_NAME] = OLAFilter(OLAGuiSetup.SHEET_VIEW_FILTER_TAG, self.applyFilter)
        self.filters[OLAGui.REPORTS_TAB_NAME] = OLAFilter(OLAGuiSetup.REPORT_VIEW_FILTER_ID, self.applyFilter, searchEnabled=False)
        self.filter = self.defaultFilter

        self.layout().addWidget(self.defaultFilter)
        self.layout().addWidget(self.filters[OLAGui.SESSIONS_TAB_NAME])
        self.filters[OLAGui.SESSIONS_TAB_NAME].setVisible(False)
        self.layout().addWidget(self.filters[OLAGui.ASSISTANT_TAB_NAME])
        self.filters[OLAGui.ASSISTANT_TAB_NAME].setVisible(False)
        self.layout().addWidget(self.filters[OLAGui.REPORTS_TAB_NAME])
        self.filters[OLAGui.REPORTS_TAB_NAME].setVisible(False)

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
        OLAGui.REPORTS.applyFiltering()

    def applyCheck(self):
        OLAGui.SESSIONS.showUnlink = self.filters[OLAGui.SESSIONS_TAB_NAME].linkSelector.isChecked()
        OLAGui.SESSIONS.showOnlyInstalled = self.filters[OLAGui.SESSIONS_TAB_NAME].installSelector.isChecked()
        OLAGui.SESSIONS.showVN = self.filters[OLAGui.SESSIONS_TAB_NAME].vnSelector.isChecked()
        OLAGui.SESSIONS.showVNA = self.filters[OLAGui.SESSIONS_TAB_NAME].vnaSelector.isChecked()
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
            self.rawName = None

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
            self.menu.addAction("Localise").triggered.connect(self.doLocalise)
            self.menu.addAction("Setup Launcher").triggered.connect(self.doSetupLauncher)
            self.menu.addAction("Exclude").triggered.connect(self.doExclude)
            self.menu.addAction("Remove").triggered.connect(self.doRemove)
            self.menu.addAction("Open Folder").triggered.connect(self.openFolder)
            self.menu.addAction("Copy Name").triggered.connect(self.copyPathName)
        else:
            self.menu.addAction("Copy Name").triggered.connect(self.copySheetName)

        #Used when file selection needed
        self.dialog = None

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

    def doLocalise(self):
        # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QFileDialog.html
        if self.dialog is None:
            self.dialog = QFileDialog(self)
            self.dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            self.dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            self.dialog.setNameFilters([ "Executable (*.exe)", "Script (*.bat)", "All Files (*)" ])
            self.dialog.setWindowTitle('Select game executable...')
            self.dialog.setDirectory(OLAGuiSetup.getSetupEntry(OLAGuiSetup.DEFAULT_GAME_FOLDER))
            self.dialog.finished.connect(self.doLocaliseDone)
            self.dialog.open()

    def doLocaliseDone(self, code):
        if code == QDialog.DialogCode.Accepted:
            raw_selection = self.dialog.selectedFiles()
            self.dialog = None
            if len(raw_selection) > 0:
                selection = raw_selection[0]
                self.session.setPath(selection)
                OLAGameLine.saveOnEdit()
        self.dialog = None

    @staticmethod
    def saveOnEdit():
        OLABackend.SBSGL.procmgr.storage.save()
        OLAGui.TAB_PANEL.reload()
        OLAGui.PLAYING_PANEL.refreshSBSGL(force=True)

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
        OLAGameLine.saveOnEdit()

    def setVaultName(self):
        OLAGameLine.requestVaultNameDialog(self.session.getGameInfo(), self.sheet, GhFileUtil.ConvertUpperCaseWordSeparatedNameToStr(self.name.text()), self)

    def setSession(self, session, sheetAlreadySet=None):
        """
        :param: session: sbsbl.data.session
        """
        self.session = session
        sessionSheet = session.getSheet()
        if sheetAlreadySet:
            if self.sheet != sessionSheet:
                self.session.setSheet(self.sheet)
                OLAGameLine.saveOnEdit()
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
        self.showVN = OLAGuiSetup.DEFAULT_VN_MODE_FILTER
        self.showVNA = OLAGuiSetup.DEFAULT_VNA_MODE_FILTER

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
        try:
            sheet = OLABackend.VAULT.SHEETS[session.getSheet()]
        except :
            sheet = None
        # Discard of session with no sheet if sheet is requested by filter
        if not self.showUnlink and sheet is None:
            return False
        # Discard not installed game if only installed game should be displayed
        if self.showOnlyInstalled and not session.installed:
            return False
        # If search token is set, discard whatever do not match the earch token
        if self.filter.searchToken is not None and not self.filter.searchToken in session.getName():
            return False
        # If sheet is set, check if sheet match the filter
        if sheet is not None:
            return self.sheetMatchFilter(sheet)
        # No sheet but no filter selected -> let's display it ( game not conform to OLA )
        elif self.filter.value is None:
                return True
        # else: no  sheet, filter value is set
        elif self.showUnlink:
            return True
        else:
            return False

    def sheetMatchFilter(self, sheet):
        # if a search token is set, discard any entry that do not match
        if self.filter.searchToken is not None and not self.filter.searchToken in sheet.name:
            return False
        if self.filter.tag == OLAGuiSetup.SHEET_VIEW_FILTER_TAG:
            tags = sheet.type_tags
        elif self.filter.tag == OLAGuiSetup.SESSION_VIEW_FILTER_TAG:
            tags = sheet.play_tags
        else:
            # internal error -- all filters should have a tag set for filtering
            return True

        # Apply filter on type if requested
        if not self.showVN or not self.showVNA:
            for t in sheet.type_tags:
                if not self.showVN and t.startswith("VN/"):
                    return False
                if not self.showVNA and t.startswith("VNA"):
                    return False

        # Filtering on the combo selected value ( None: no value selected, no filtering )
        if self.filter.value is not None:
            for t in tags:
                if t.startswith(self.filter.value):
                        return True
        else:
            return True

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
        filteringNeeded = ( not self.showUnlink
                or self.showOnlyInstalled
                or self.showVN
                or self.showVNA
                or self.filter.isFiltering() )
        if filteringNeeded:
            logging.debug("Loading session with filter {} / {}".format(self.filter.tag, self.filter.value))
            selList = []
            for data in rawList:
                if self.matchFilter(data):
                    selList.append(data)
        else:
            logging.debug("Loading session without filtering")
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

class OLABaseReportLine():
    def __init__(self, sheetPath, customLabel=None, generateButtonState=True):
        super().__init__()

        self.sheet = sheetPath

        if sheetPath != "":
            bVault = QPushButton("")
            bVault.setStatusTip("Open in obsidian Vault")
            bVault.setIcon(Icons.OBSIDIAN)
            bVault.clicked.connect(self.openReportInVault)
            # bVault.setEnabled(False)
            self.bVault = bVault

        if customLabel is None:
            bRedo = QPushButton("")
            bRedo.setStatusTip("Regenerate only this report")
            bRedo.setIcon(Icons.REPORT)
            bRedo.clicked.connect(self.startSingleReport)
            bRedo.setEnabled(generateButtonState)
            self.bRedo = bRedo
        else:
            self.bRedo = None

    def openReportInVault(self):
        OLABackend.openInVault(sheetName=self.sheet)

    def startSingleReport(self):
        OLAGui.APP.startSingleReport(self.sheet)

    def disableGenerate(self):
        if self.bRedo is not None:
            self.bRedo.setEnabled(False)

    def enableVault(self):
        self.bVault.setEnabled(True)
        if self.bRedo is not None:
            self.bRedo.setEnabled(True)

    def regenerateReport(self):
        OLAGui.APP.startSingleReport(self.sheet)

class OLAReportLine(OLABaseReportLine):
    def __init__(self, row, col, layout, sheetPath, reportData, customLabel=None, generateButtonState=True):
        super().__init__(sheetPath, customLabel, generateButtonState)
        self.sheetMaxLen = 40
        if col == 2:
            layout.addWidget(QLabel(" | "), row, 2)
            colUpdated = 3
        elif col == 5:
            layout.addWidget(QLabel(" | "), row, 5)
            colUpdated = 6
        elif col == 8:
            layout.addWidget(QLabel(" | "), row, 8)
            colUpdated = 9
        else:
            colUpdated = col

        if customLabel is None:
            self.sname = os.path.basename(sheetPath)
            self.sname = self.sname[0:len(self.sname) - 3]
            sheet = QLabel(reportData["name"])
            tips = "{} ({})".format(reportData["about"], self.sname)
        else:
            self.sname = customLabel
            sheet = QLabel(customLabel)
            tips = reportData["about"]
        sheet.setToolTip(tips)
        # Sheet adjustement to be less "disaligned"
        current = sheet.text()
        if len(current)>self.sheetMaxLen:
            current = "{}...".format(current[0:self.sheetMaxLen])
        else:
            current = current + ' ' * ( self.sheetMaxLen - len(current))
        sheet.setText(current)
        layout.addWidget(sheet, row, colUpdated)

        bPanel = QWidget()
        bPanel.setLayout(QHBoxLayout())
        bPanel.layout().setContentsMargins(0, 0, 0, 0)

        if sheetPath != "":
            bPanel.layout().addWidget(self.bVault)

        if customLabel is None:
            bPanel.layout().addWidget(self.bRedo)

        self.countLabel = QLabel("")
        bPanel.layout().addWidget(self.countLabel)
        layout.addWidget(bPanel, row, 1)
        self.refreshSize()

        bPanel.layout().addStretch()

        layout.addWidget(bPanel, row, colUpdated + 1)

    def refreshSize(self):
        self.countLabel.setText("{}".format(OLABackend.VAULT.REPORT_INFO.get(self.sname)))

class OLADetailedReportLine(OLABaseReportLine):
    def __init__(self, row, layout, sheetPath, reportData, customLabel=None, generateButtonState=True):
        super().__init__(sheetPath, customLabel, generateButtonState)

        bPanel = QWidget()
        bPanel.setLayout(QHBoxLayout())
        bPanel.layout().setContentsMargins(0, 0, 0, 0)

        if sheetPath != "":
            bPanel.layout().addWidget(self.bVault)

        if customLabel is None:
            bPanel.layout().addWidget(self.bRedo)

        self.countLabel = QLabel("")
        bPanel.layout().addWidget(self.countLabel)
        layout.addWidget(bPanel, row, 1)

        notes = ""
        if customLabel is None:
            sheet = QLabel(reportData["name"])
            self.sname = os.path.basename(sheetPath)
            self.sname = self.sname[0:len(self.sname) - 3]
            notes = OLABackend.VAULT.NOTES.get(self.sname)
        else:
            sheet = QLabel(customLabel)
        sheet.setStyleSheet(OLAGuiSetup.STYLE_QLABEL_TITLE)
        layout.addWidget(sheet, row, 2)
        self.refreshSize()

        aboutL = QLabel(reportData["about"])
        layout.addWidget(aboutL, row, 3)

        bPanel = QWidget()
        bPanel.setLayout(QHBoxLayout())
        bPanel.layout().setContentsMargins(0, 0, 0, 0)
        bPanel.layout().addStretch()
        layout.addWidget(bPanel, row, 4)

        mdFile = QLabel(self.sname)
        mdFile.setStyleSheet(OLAGuiSetup.STYLE_QLABEL_EXTRAINFO)
        layout.addWidget(mdFile, row + 1, 2)

        self.info = QLineEdit()
        self.info.setText(notes)
        self.noteEdited = False
        self.info.setStyleSheet(OLAGuiSetup.STYLE_QLINE_EDITABLE)
        self.info.textChanged.connect(self.noteTextUpdated)
        self.info.editingFinished.connect(self.noteTextFinished)
        layout.addWidget(self.info, row + 1, 3)

        bDesc = QPushButton("")
        bDesc.setStatusTip("Show report explanation")
        bDesc.setIcon(Icons.QUESTION)
        bDesc.clicked.connect(self.showHideDescription)
        layout.addWidget( bDesc, row+1, 1)

        self.desc = QLabel(reportData["description"])
        self.desc.setStyleSheet(OLAGuiSetup.STYLE_QLABEL_COMMENT)
        self.desc.setVisible(False)
        layout.addWidget( self.desc, row+3, 3)

    def refreshSize(self):
        self.countLabel.setText("{}".format(OLABackend.VAULT.REPORT_INFO.get(self.sname)))

    def showHideDescription(self):
        self.desc.setVisible(not self.desc.isVisible())

    def noteTextUpdated(self):
        if not self.noteEdited:
            self.info.setStyleSheet(OLAGuiSetup.STYLE_QLINE_EDITED)
            self.noteEdited = True

    def noteTextFinished(self):
        self.info.setStyleSheet(OLAGuiSetup.STYLE_QLINE_EDITABLE)
        self.noteEdited = False
        if self.sname is not None:
            OLABackend.VAULT.NOTES.set(self.sname, self.info.text())
            OLABackend.VAULT.NOTES.save()


class OLAReports(QWidget):
    def __init__(self, generateButtonState=True):
        super().__init__()
        OLAGui.REPORTS = self
        self.reports = dict()
        self.reportsDetailed = dict()
        self.reportsPanel = dict()
        self.reportsPanelDetailed = dict()
        self.reportLines = []
        self.currentFiltering = None
        self.start = time.time()

        layout = QVBoxLayout()
        self.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(OLAGuiSetup.VISIBLE_SESSION_COUNT)

        reportPanel = QWidget()
        self.reportPanelLayout = QVBoxLayout()
        reportPanel.setLayout(self.reportPanelLayout)
        reportPanel.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(reportPanel)

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

        if OLABackend.VAULT.reports is not None:
            OLAGui.REPORTS.setReports(OLABackend.VAULT.reports, generateButtonState=generateButtonState)

    def reportAvailable(self, name, sheetPath):
        self.setStatus("{} ({}) generated".format(name, sheetPath))
        self.reports[sheetPath].enableVault()

    def setStatus(self, message):
        elapsed = str(round(time.time() - self.start, 1))
        self.reportStatus.setText("{}s | {}".format(elapsed, message))
        for r in self.reportLines:
            r.refreshSize()

    def setLinkCheckStatus(self, message, detailed=None):
        self.linkErrorMessage.setText(message)
        if detailed is None:
            self.linkErrorMessage.setToolTip("")
        else:
            self.linkErrorMessage.setToolTip("\n".join(detailed))

    def disableGeneration(self):
        for line in self.reports.values():
            try:
                line.disableGenerate()
            except AttributeError:
                pass

    def applyFiltering(self):
        OLAGui.REPORTS.setReports(OLABackend.VAULT.reports)

    def createGroupBox(self, group, sheetPaths, reportsList, reportPanelsList):
        groupPanel = QGroupBox()
        groupPanelLayout = QGridLayout()
        groupPanel.setLayout(groupPanelLayout)
        reportPanelsList[group] = groupPanel
        if len(sheetPaths) > 0:
            extraInfo = " - {} reports".format(len(sheetPaths))
        else:
            extraInfo = ""
        reportsList[group] = QLabel("{}{}".format(group, extraInfo))
        reportsList[group].setStyleSheet(OLAGuiSetup.STYLE_QLABEL_TITLE)
        self.reportPanelLayout.addWidget(reportsList[group])
        self.reportPanelLayout.addWidget(groupPanel)

        return groupPanelLayout

    def addDetailedReportGroup(self, group, sheetPaths, generateButtonState=False):
        groupPanelLayout = self.createGroupBox(group, sheetPaths, self.reportsDetailed, self.reportsPanelDetailed)
        row = 0
        for sheetPath, data in sheetPaths.items():
            self.reportsDetailed[sheetPath] = OLADetailedReportLine(row, groupPanelLayout, sheetPath, data, generateButtonState=generateButtonState)
            self.reportLines.append(self.reportsDetailed[sheetPath])
            row = row + 4

    def addReportGroup(self, group, sheetPaths, generateButtonState=False):
        groupPanelLayout = self.createGroupBox(group, sheetPaths, self.reports, self.reportsPanel)

        col = 0
        row = 0
        for sheetPath, data in sheetPaths.items():
            self.reports[sheetPath] = OLAReportLine(row, col, groupPanelLayout, sheetPath, data, generateButtonState=generateButtonState)
            self.reportLines.append(self.reports[sheetPath])
            if col == 0:
                col = 2
            elif col == 2:
                col = 5
#            elif col == 5:
#                col = 8
            else:
                row = row + 1
                col = 0
        return groupPanelLayout

    def setReports(self, sheetPathsByGroup, generateButtonState=False):
        selectedGroup = OLAGui.PLAYING_PANEL.filters[OLAGui.REPORTS_TAB_NAME].value
        if selectedGroup is not None and len(selectedGroup) == 0:
            selectedGroup = None

        if len(self.reportsPanel) == 0: # 1st call : init all widgets
            for group, sheetPaths in sheetPathsByGroup.items():
                self.addDetailedReportGroup(group, sheetPaths, generateButtonState)
                self.addReportGroup(group, sheetPaths, generateButtonState)
            groupPanelLayout = self.addReportGroup("Files", dict(), generateButtonState)
            tmpData = dict()
            tmpData["about"] = "Report that identify duplicate files in predefined folders"
            self.reports["Duplicate files"] = OLAReportLine(1, 0, groupPanelLayout, OLABackend.VAULT.REPORTS_DUPFILE_NAME, tmpData,
                                                        customLabel="Files duplication")
            self.reportPanelLayout.addStretch()

        for group in sheetPathsByGroup.keys():
            # hide all
            self.reportsPanelDetailed[group].setVisible(False)
            self.reportsDetailed[group].setVisible(False)

            self.reportsPanel[group].setVisible(False)
            self.reports[group].setVisible(False)

            # display only what applicable
            if selectedGroup == group:
                self.reportsPanelDetailed[group].setVisible(True)
                self.reportsDetailed[group].setVisible(True)
            elif selectedGroup is None:
                self.reportsPanel[group].setVisible(True)
                self.reports[group].setVisible(True)

        if selectedGroup is None:
                self.reportsPanel["Files"].setVisible(True)
                self.reports["Files"].setVisible(True)
        else:
                self.reportsPanel["Files"].setVisible(False)
                self.reports["Files"].setVisible(False)


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

    def vaultAllReportsInProgress(self):
        self.title = "Vault all reports generation in progress"
        self.col1.setText(self.title)

    def vaultParsingInProgress(self):
        self.title = "Vault loading in progress"
        self.col1.setText(self.title)

    def vaultParsed(self):
        OLALock.releaseMDEngine()
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
        self.declareTab(OLAReports(), OLAGui.REPORTS_TAB_NAME)
        #self.declareTab(OLAExcludedGame(), OLAGui.EXCLUDED_TAB_NAME)

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

    def clearReportsTab(self):
        OLAGui.PLAYING_PANEL.filters[OLAGui.REPORTS_TAB_NAME].setNoSelection()
        OLAGui.REPORTS.disableGeneration()
        OLAGui.REPORTS.applyFiltering()

    def showReportsTab(self):
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

        size = self.geometry()
        posx = OLAGuiSetup.getSetupEntry(OLAGuiSetup.POSX)
        posy = OLAGuiSetup.getSetupEntry(OLAGuiSetup.POSY)
        # TODO Check this is really visible...
        height = OLAGuiSetup.getSetupEntry(OLAGuiSetup.HEIGHT)
        if height < size.height():
            height = size.height()
        width = OLAGuiSetup.getSetupEntry(OLAGuiSetup.WIDTH)
        if width < size.width():
            width = size.width()
        logging.info("OLAMainWindow - initial position from setup file: {},{} and size {} * {}\nNote : Edit configuration file <HOMEDIR>/ola.json if startup position windows is not visible due to screen configuration change."
                     .format(posx, posy, height, width))
        self.move( posx, posy )
        self.resize( width, height )

        self.status = OLAStatusBar()
        self.setStatusBar(self.status)
        self.status.set("Loading in progress...")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = OLAToolbar()
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

    def storeGuiState(self, olaSetup):
        size = self.geometry()
        olaSetup.set(OLAGuiSetup.POSX, self.x())
        olaSetup.set(OLAGuiSetup.POSY, self.y())
        olaSetup.set(OLAGuiSetup.HEIGHT, size.height())
        olaSetup.set(OLAGuiSetup.WIDTH, size.width())

class OLAApplication(QApplication):

    def __init__(self, argv, version):
        super().__init__(argv)

        self.olaSetup = OLAGuiSetup(True)
        Icons.initIcons()

        self.splash = QSplashScreen(Icons.SPLASH)
        self.splash.showMessage("{} - loading vault...".format(OLAVersionInfo.VERSION))
        self.splash.show()
        self.processEvents()

        # Blocking parsing of vault or display will be wrong
        mdgen = MdReportGenerator(allReports=False, initReportsList=True)
        mdgen.run()

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
        self.scanRejected = 0

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
            self.scanRejected = 0
            proc = SgSGLProcessScanner()
            proc.signals.refresh_finished.connect(self.scanFinished)
            self.threadpool.start(proc)
        else:
            OLAGui.MAIN.setStatus("/!\\ game process scan rejected")
            self.scanRejected = self.scanRejected + 1
            if self.scanRejected == 2:
                logging.warning("Too many scan process rejected, reset the protection")
                self.scanRejected = 0
                self.scanInProgress = False

    def shutdown(self):
        self.main.storeGuiState(self.olaSetup)
        self.olaSetup.save()
        QCoreApplication.quit()

    def parseVault(self):
        if OLALock.takeMdEngine():
            OLAGui.ASSISTANT.vaultParsingInProgress()
            mdgen = MdReportGenerator(allReports=False)
            mdgen.signals.md_report_generation_finished.connect(self.mdParsed)
            self.threadpool.start(mdgen)
        else:
            OLAGui.MAIN.setStatus("Obsidian Vault engine already running")

    def startReporting(self):
        if OLALock.takeMdEngine():
            if OLAGui.REPORTS is not None:
                OLAGui.REPORTS.start = time.time()
            OLAGui.TAB_PANEL.clearReportsTab()
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
        else:
            OLAGui.MAIN.setStatus("Vault engine already running")

    def startSingleReport(self, target):
        OLAGui.REPORTS.start = time.time()
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
        OLAGui.REPORTS.reportAvailable(reportName, sheet)

    def mdParsed(self):
        self.checkSplash()
        self.main.setStatus("Vault parsed")
        OLAGui.ASSISTANT.vaultParsed()
        OLAGui.SESSIONS.loadSessions()
        OLAGui.PLAYING_PANEL.refreshVault()

    def mdStarting(self, reports):
        OLAGui.TAB_PANEL.showReportsTab()
        OLAGui.ASSISTANT.vaultAllReportsInProgress()

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
