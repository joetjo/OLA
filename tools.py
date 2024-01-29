import logging

from PySide6.QtCore import QRunnable, Slot, QObject, Signal

from diskAnalyser.DiskAnalyser import DiskAnalyser
from markdownHelper.markdown import MarkdownHelper


class MdReportGeneratorSignals(QObject):
    md_report_generation_finished = Signal()


class FileUsageGeneratorSignals(QObject):
    file_usage_generation_finished = Signal()


class MdReportGenerator(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = MdReportGeneratorSignals()

    @Slot()  # QtCore.Slot
    def run(self):
        try:
            logging.info("Starting Markdown report generation")
            MarkdownHelper(vault="C:\\Users\\nicol\\Documents\\GitHub\\gList2").generateAllReports()
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