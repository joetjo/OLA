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
import re
import subprocess

from PySide6.QtCore import QRunnable, Slot, QObject, Signal

from base.fileutil import GhFileUtil
from base.osutil import OSUtil
from diskAnalyser.DiskAnalyser import DiskAnalyser
from markdownHelper.markdown import MarkdownHelper


class OLABackend:
    SBSGL = None
    VAULT = None
    VAULT_READY = False
    THPOOL = None

    @staticmethod
    def openInVault(fullpath=None, sheetName=None):
        if fullpath is None:
            path = "{}%2F{}".format(OLABackend.VAULT.VAULT.replace(" ", "%20").replace("\\", "%2F"),
                                    sheetName).replace(" ", "%20")
        else:
            path = fullpath
        url = "obsidian://open?path={}".format(path)
        logging.info("opening {}".format(url))
        OSUtil.systemOpen(url)


class LauncherSignals(QObject):
    ok = Signal()
    ko = Signal()


class MdReportGeneratorSignals(QObject):
    md_report_generation_finished = Signal()
    md_report_generation_failure = Signal(object)
    md_report_generation_starting = Signal(object)
    md_last_report = Signal(object, object)


class FileUsageGeneratorSignals(QObject):
    file_usage_generation_finished = Signal()
    sheet_link_progress = Signal(object)
    sheet_link_finished = Signal(object, object, object, object, object)


class SbSGLSignals(QObject):
    refresh_finished = Signal()
    refresh_done = Signal(object, object, object)
    game_started = Signal(object)
    game_ended = Signal(object)


class MdReportGenerator(QRunnable):
    def __init__(self, allReports=True, target=None):
        super().__init__()
        self.signals = MdReportGeneratorSignals()
        self.allReports = allReports
        self.target = target

    @Slot()  # QtCore.Slot
    def run(self):
        try:
            logging.info("Starting Markdown report generation")
            OLABackend.VAULT = MarkdownHelper(vault="J:\\Nicol-Documents\\GitHub\\gList2")
            if self.allReports:
                OLABackend.VAULT.generateAllReports(self.signals.md_report_generation_starting, self.signals.md_last_report, reload=True)
                logging.info("Generation Markdown reports finished")
            elif self.target is not None:
                OLABackend.VAULT.generateReport(self.target, self.signals.md_report_generation_starting, self.signals.md_last_report)
                logging.info("Generation Markdown single report finished")
            else:
                OLABackend.VAULT.parseVault()
                logging.info("Parse Vault finished")
                OLABackend.VAULT_READY = True
        finally:
            self.signals.md_report_generation_finished.emit()


class FileUsageGenerator(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = FileUsageGeneratorSignals()

    @Slot()  # QtCore.Slot
    def run(self):
        try:
            logging.info("Starting File Usage generation")
            DiskAnalyser().generateReport()
            logging.info("Generation File Usage finished")

            count = 0
            linkCount = 0
            brokenLink = 0
            repairedLink = 0
            names = []
            sessions = OLABackend.SBSGL.procmgr.getSessions()
            sessionsCount = len(sessions)
            self.signals.sheet_link_progress.emit("Checking {} vault links...".format(sessionsCount))
            for session in sessions:
                sheet = session.getGameInfo()['sheet']
                # STEP 1 - check if current sheet seems to exist
                if sheet is not None and len(sheet) > 0:
                    find = GhFileUtil.findFileInFolder("{}.md".format(sheet), OLABackend.VAULT.VAULT)
                    if find:
                        linkCount = linkCount + 1
                    else:
                        logging.warning("Broken vault link detected : {}".format(sheet))
                        names.append("- [{}]".format(sheet))
                        brokenLink = brokenLink + 1
                        session.getGameInfo()['sheet'] = ""
                # STEP 2 - test if empty sheet could be guessed from current sheet name
                sheet = session.getGameInfo()['sheet']
                if sheet is None or len(sheet) == 0:
                    sheet = "{}.md".format(session.json[0])
                    find = GhFileUtil.findFileInFolder(sheet, OLABackend.VAULT.VAULT)
                    if find is None:
                        sheet = GhFileUtil.ConvertUpperCaseWordSeparatedNameToStr(sheet)
                        find = GhFileUtil.findFileInFolder(sheet, OLABackend.VAULT.VAULT)
                    if find:
                        repairedLink = repairedLink + 1
                        session.getGameInfo()['sheet'] = sheet[0:len(sheet) - 3]
                        names.append("+ [{}]".format(session.getGameInfo()['sheet']))

                count = count + 1
                if count % 10 == 0:
                    self.signals.sheet_link_progress.emit("{}/{} links checked...".format(count, sessionsCount))

            if brokenLink > 0 or repairedLink > 0:
                OLABackend.SBSGL.procmgr.storage.save()
            self.signals.sheet_link_finished.emit(sessionsCount, linkCount, brokenLink, repairedLink, names)
        finally:
            self.signals.file_usage_generation_finished.emit()


class SgSGLProcessScanner(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = SbSGLSignals()

    @Slot()  # QtCore.Slot
    def run(self):
        try:
            OLABackend.SBSGL.procmgr.refresh()
        finally:
            self.signals.refresh_finished.emit()


class SgSGLLauncher(QRunnable):
    def __init__(self, label, exe, cwd=os.getcwd()):
        super().__init__()
        self.label = label
        self.exe = exe
        self.cwd = cwd
        self.signals = LauncherSignals()

    @Slot()  # QtCore.Slot
    def run(self):
        signalSend = False
        try:
            subprocess.run(self.exe, cwd=self.cwd)
            self.signals.ok.emit()
            signalSend = True
        except FileNotFoundError:
            logging.error("Unable to launch {} missing executable {} in folder {}".format(self.label, self.exe, self.cwd))
        finally:
            if not signalSend:
                self.signals.ko.emit()
