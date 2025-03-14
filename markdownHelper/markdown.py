# Copyright 2023 joetjo https://github.com/joetjo/MarkdownHelper
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

from base.setup import GhSetup

from pathlib import Path

from markdownHelper.markdownfile import MhMarkdownFile
from markdownHelper.report import MhReport, MhReportDescriptionSheet


#
# Setup from $home/.markdownHelper
#    ( Sample provided in example.markdownHelper.json )
#
class MarkdownHelper:
    def __init__(self, vault=None, playtag="#PLAY/INPROGRESS"):
        self.SETUP = GhSetup('markdownHelper')
        if vault is not None:
            self.VAULT = vault
        else:
            self.VAULT = self.SETUP.getBloc("global")["base_folder"]
        self.REPORTS_SHEET_NAME = self.SETUP.getBloc("global")["reports_readme"]
        self.REPORTS_DUPFILE_NAME = self.SETUP.getBloc("global")["reports_dupfiles"]
        self.vaultLenPath = len(self.VAULT) + 1
        self.playtag = playtag
        self.IGNORE = self.SETUP.getBloc("global")["ignore"]
        self.REPORTS = self.SETUP.getBloc("global")["reports"]
        self.SUBCONTENT = self.SETUP.getBloc("global")["shared_contents"]
        self.FILES = dict()
        self.PLAY = []
        self.SHEETS = dict()
        self.SORTED_FILES = dict()
        self.TAGS = dict()
        self.TYPE_TAGS_UNSORTED = set()
        self.TYPE_TAGS = []
        self.PLAY_TAGS_UNSORTED = set()
        self.PLAY_TAGS = []
        self.REPORTS_SHEET = MhReportDescriptionSheet("# Reports description\n\n> Automatic reports description\n", self.REPORTS_SHEET_NAME)

    # folder: Path
    # shift: String ( String length provide the indentation level )
    def processFolder(self, folder, shift):
        logging.debug("MDR | {}{}".format(folder, shift))
        entryCount = 0

        # Loop on file in current folder
        for entry in folder.iterdir():
            if entry.is_file() and entry.name.endswith(".md") and entry.name not in self.IGNORE:
                key = entry.name[0:len(entry.name) - 3]
                entryCount = entryCount + 1
                mdfile = MhMarkdownFile(key, entry, self.vaultLenPath)
                self.FILES[key] = mdfile
                logging.debug("MDR | {}>{} {}".format(shift, key.encode("utf-8"), mdfile.tags))
                if len(mdfile.tagsComment) > 0:
                    logging.debug("MDR | {}>>>> comments {}".format(shift, mdfile.tagsComment).encode("utf-8"))
                playInProgress = False
                for tag in mdfile.tags:
                    self.TAGS[tag] = tag
                    if tag == self.playtag:
                        self.PLAY.append(mdfile)
                        playInProgress = True
                    self.SHEETS[key] = mdfile
                for tag in mdfile.tags:
                    if playInProgress and tag.startswith("#TYPE/"):  # List of TYPE tag used ( combo contents in tab Obsidian )
                        self.TYPE_TAGS_UNSORTED.add(tag[6:])
                    if tag.startswith("#PLAY/"):  # List in PLAY possible values ( combo contents in tab Session )
                        self.PLAY_TAGS_UNSORTED.add(tag[6:])

        # Loop on sub folder
        for entry in folder.iterdir():
            if not entry.is_file() and entry.name not in self.IGNORE:
                entryCount = entryCount + self.processFolder(entry, "{}{}".format(shift, " "))

        return entryCount

    def parseVault(self):
        logging.info("MDR | Markdown vault: {}".format(self.VAULT))
        count = self.processFolder(Path(self.VAULT), "")

        logging.info("MDR | > {} md files detected".format(count))
        logging.info("MDR | > {} tags detected".format(len(self.TAGS)))

        for key in sorted(self.FILES):
            self.SORTED_FILES[key] = self.FILES[key]

        for t in sorted(self.TYPE_TAGS_UNSORTED):
            self.TYPE_TAGS.append(t)

        for t in sorted(self.PLAY_TAGS_UNSORTED):
            self.PLAY_TAGS.append(t)

    def processReport(self, reportTitle, report, current, total, signal_report):
        logging.info("MDR | Processing report \"{}\" {}/{}".format(reportTitle, current, total))
        sname = os.path.basename(report["target"])
        sname = sname[0:len(sname) - 3]
        try:
            ctag = report["commentTag"]
        except KeyError:
            ctag = "X"
        self.REPORTS_SHEET.addTarget(reportTitle, sname, ctag)
        report["title"] = reportTitle
        MhReport(report, self.VAULT, self.SORTED_FILES, self.TAGS, self.SUBCONTENT, self.REPORTS_SHEET).generate()

        with open("{}/{}".format(self.VAULT, self.REPORTS_SHEET_NAME), 'w', encoding='utf-8') as writer:
            for line in self.REPORTS_SHEET.lines:
                writer.writelines(line)
        signal_report.emit(reportTitle, report["target"])

    def generateReport(self, target, signal_reports, signal_report):
        self.parseVault()

        for reportTitle, report in self.REPORTS.items():
            if report["target"] == target:
                self.processReport(reportTitle, report, 1, 1, signal_report)

    def generateAllReports(self, signal_reports, signal_report, reload=False):
        try:
            if reload or len(self.SORTED_FILES) == 0:
                self.parseVault()

            total = len(self.REPORTS)
            reportTargets = dict()

            for report in self.REPORTS.values():
                try:
                    about = report["about"]
                except KeyError:
                    about = "no description available..."
                reportTargets[report["target"]] = about
            signal_reports.emit(reportTargets)

            current = 1
            for reportTitle, report in self.REPORTS.items():
                self.processReport(reportTitle, report, current, total, signal_report)
                current = current + 1

        except Exception as e:
            raise e
