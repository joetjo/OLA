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

from PySide6.QtCore import QRunnable, Slot, QObject, Signal

from diskAnalyser.DiskAnalyser import DiskAnalyser
from markdownHelper.markdown import MarkdownHelper


class OLABackend:
    SBSGL = None


class MdReportGeneratorSignals(QObject):
    md_report_generation_finished = Signal()
    md_last_report = Signal(object)


class FileUsageGeneratorSignals(QObject):
    file_usage_generation_finished = Signal()


class SbSGLSignals(QObject):
    refresh_finished = Signal()
    refresh_done = Signal(object, object, object)  # TODO NOT USED Listener
    game_started = Signal(object)  # TODO NOT USED Listener
    game_ended = Signal(object)  # TODO NOT USED Listener


class MdReportGenerator(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = MdReportGeneratorSignals()

    @Slot()  # QtCore.Slot
    def run(self):
        try:
            logging.info("Starting Markdown report generation")
            MarkdownHelper(vault="C:\\Users\\nicol\\Documents\\GitHub\\gList2").generateAllReports(self.signals.md_last_report)
            logging.info("Generation Markdown report finished")
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
