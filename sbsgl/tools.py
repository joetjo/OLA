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

from PySide6.QtCore import QRunnable, Slot, QObject, Signal

from diskAnalyser.DiskAnalyser import DiskAnalyser
from markdownHelper.markdown import MarkdownHelper


class OLABackend:
    SBSGL = None
    VAULT = None
    THPOOL = None


class LauncherSignals(QObject):
    ok = Signal()
    ko = Signal()


class MdReportGeneratorSignals(QObject):
    md_report_generation_finished = Signal()
    md_last_report = Signal(object)


class FileUsageGeneratorSignals(QObject):
    file_usage_generation_finished = Signal()


class SbSGLSignals(QObject):
    refresh_finished = Signal()
    refresh_done = Signal(object, object, object)
    game_started = Signal(object)
    game_ended = Signal(object)


class MdReportGenerator(QRunnable):
    def __init__(self, report=True):
        super().__init__()
        self.signals = MdReportGeneratorSignals()
        self.report = report

    @Slot()  # QtCore.Slot
    def run(self):
        try:
            logging.info("Starting Markdown report generation")
            OLABackend.VAULT = MarkdownHelper(vault="C:\\Users\\nicol\\Documents\\GitHub\\gList2")
            if self.report:
                OLABackend.VAULT.generateAllReports(self.signals.md_last_report, reload=True)
                logging.info("Generation Markdown report finished")
            else:
                OLABackend.VAULT.parseVault()
                logging.info("Parse Vault finished")
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