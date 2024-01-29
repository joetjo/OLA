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

from base.setup import GhSetup

from pathlib import Path

from markdownHelper.markdownfile import MhMarkdownFile
from markdownHelper.report import MhReport


#
# Setup from $home/.markdownHelper
#    ( Sample provided in example.markdownHelper.json )
#
class MarkdownHelper:
    def __init__(self, vault=None):
        self.SETUP = GhSetup('markdownHelper')
        if vault is not None:
            self.VAULT = vault
        else:
            self.VAULT = self.SETUP.getBloc("global")["base_folder"]
        self.IGNORE = self.SETUP.getBloc("global")["ignore"]
        self.REPORTS = self.SETUP.getBloc("global")["reports"]
        self.SUBCONTENT = self.SETUP.getBloc("global")["shared_contents"]
        self.FILES = dict()
        self.SORTED_FILES = dict()
        self.TAGS = dict()

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
                mdfile = MhMarkdownFile(key, entry)
                self.FILES[key] = mdfile
                logging.debug("MDR | {}>{} {}".format(shift, key, mdfile.tags))
                if len(mdfile.tagsComment) > 0:
                    logging.debug("MDR | {}>>>> comments {}".format(shift, mdfile.tagsComment))
                for tag in mdfile.tags:
                    self.TAGS[tag] = tag

        # Loop on sub folder
        for entry in folder.iterdir():
            if not entry.is_file() and entry.name not in self.IGNORE:
                entryCount = entryCount + self.processFolder(entry, "{}{}".format(shift, " "))

        return entryCount

    def generateAllReports(self):
        logging.info("MDR | Markdown vault: {}".format(self.VAULT))
        count = self.processFolder(Path(self.VAULT), "")

        logging.info("MDR | > {} md files detected".format(count))
        logging.info("MDR | > {} tags detected".format(len(self.TAGS)))

        for key in sorted(self.FILES):
            self.SORTED_FILES[key] = self.FILES[key]

        try:
            total = len(self.REPORTS)
            current = 1
            for report in self.REPORTS:
                logging.info("MDR | Processing report \"{}\" {}/{}".format(report["title"], current, total))
                current = current + 1
                MhReport(report, self.VAULT, self.SORTED_FILES, self.TAGS, self.SUBCONTENT).generate()
        except Exception as e:
            raise
