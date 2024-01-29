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
from datetime import datetime

# Ugly but simple
from markdownHelper.label import MhLabels

LONG_BLANK = "                                                                                                         "

ALLOWED_ATTRIBUTES = ["target",  # 1st level only: target file path
                      "title",  # mandatory on each bloc
                      "tag_condition",  # optional: tag list to filter content ( can be tag prefix )
                      "path_condition",  # optional: name list that should be used in folder path
                      "tag_not_condition",  # optional: tag list to filter content ( can be tag prefix ) ONLY IN COUNT BLOC
                      "path_not_condition",  # optional: name list that should be used in folder path ONLY IN COUNT BLOC
                      "condition_type",  # if "not" --> inverse the tag_condition or path condition
                      "multi_condition",  # "or" by default. can be set to "and"
                      "contents",  # sub blocs / in not defined --> leaf to print
                      "count",  # sub blocs / statistic bloc
                      "content_ref",  # reference to a "shared content definition" under shared_contents node
                      "else",  # optional: bloc to process all entries not selected by filter
                      "commentTag",  # a comment TAG is a tag that start at the beginning of the line and
                      # the text on the same line will be registered as a comment and shown in report.
                      "showTags",  # tag that start by the requested string will be added to the line
                      "labelAbout",
                      "labelTags",
                      "labelComment"
                      ]


class UnknownJSonAttribute(Exception):
    def __init__(self, attName, json,
                 message="Unknown JSon attribute \"{}\" used in report, allowed attributes are: {}, json bloc:\n{}"):
        self.message = message
        super().__init__(self.message.format(attName, ALLOWED_ATTRIBUTES, json))


class UnknownContentRef(Exception):
    def __init__(self, ref, json,
                 message="Unknown content reference \"{}\" used, json bloc:\n{}"):
        self.message = message
        super().__init__(self.message.format(ref, json))


class MhCountEntry:

    def __init__(self, json, inputFiles):
        self.json = json
        self.inputFiles = inputFiles
        self.count = 0

        for key in json:
            if key not in ALLOWED_ATTRIBUTES:
                raise UnknownJSonAttribute(key, json)

        # Setup content filter
        try:
            self.tags = self.json["tag_condition"]
        except KeyError:
            self.tags = []

        try:
            self.not_tags = self.json["tag_not_condition"]
        except KeyError:
            self.not_tags = []

        try:
            self.paths = self.json["path_condition"]
        except KeyError:
            self.paths = []

        try:
            self.not_paths = self.json["path_not_condition"]
        except KeyError:
            self.not_paths = []

        for name, file in self.inputFiles.items():
            if self.matchCondition(file):
                self.count = self.count + 1

    # Returns True if file match report condition
    def matchCondition(self, file):
        resultByTag = True
        resultByPath = True
        resultByNotTag = True
        resultByNotPath = True

        for tag in self.tags:
            if not file.hasTagStartingBy(tag):
                resultByTag = False
                break

        for tag in self.not_tags:
            if file.hasTagStartingBy(tag):
                resultByNotTag = False
                break

        for path in self.paths:
            if not file.pathMatch(path):
                resultByPath = False
                break

        for path in self.not_paths:
            if file.pathMatch(path):
                resultByNotPath = False
                break

        return resultByTag and resultByPath and resultByNotTag and resultByNotPath

    def getCount(self):
        return self.count


class MhReportEntry:

    # inputFiles: dict of name, MhMarkdownFiles
    def __init__(self, json, inputFiles, allTags, allSubContents, commentTag, showTags, labels=None, level="#"):
        self.json = json
        self.level = level
        self.inputFiles = inputFiles
        self.allTags = allTags
        self.allSubContents = allSubContents
        self.commentTag = commentTag
        self.showTags = showTags
        if labels is None:
            self.labels = MhLabels(json)
        else:
            self.labels = labels

        for key in json:
            if key not in ALLOWED_ATTRIBUTES:
                raise UnknownJSonAttribute(key, json)

        # Setup content filter
        try:
            self.tags = self.json["tag_condition"]
        except KeyError:
            self.tags = []

        try:
            self.paths = self.json["path_condition"]
        except KeyError:
            self.paths = []

        try:
            self.inverseCondition = self.json["condition_type"]
            if self.inverseCondition != "not":
                raise UnknownJSonAttribute("condition_type", json,
                                           message="Invalid value \"{}\" for attribute \"condition_type\""
                                           .format(self.inverseCondition))
        except KeyError:
            self.inverseCondition = []

        try:
            self.multiCondition = self.json["multi_condition"]
            if self.multiCondition != "or" and self.multiCondition != "and":
                raise UnknownJSonAttribute("condition_type", json,
                                           message="Invalid value \"{}\" for attribute \"multi_condition\""
                                           .format(self.multiCondition))
        except KeyError:
            self.multiCondition = "or"

        self.isFiltering = not len(self.tags) == 0 or not len(self.paths) == 0
        self.isVirtual = self.title() == "%TAGNAME%"
        self.isRoot = level == "#"

        # Setup content
        self.elseFiles = dict()
        if not self.isFiltering:
            self.filteredFiles = inputFiles.copy()
        else:
            self.filteredFiles = dict()
            for name, file in self.inputFiles.items():
                if self.matchCondition(file):
                    self.filteredFiles[name] = file
                else:
                    self.elseFiles[name] = file

        if self.inverseCondition == "not":
            tmp = self.filteredFiles
            self.filteredFiles = self.elseFiles
            self.elseFiles = tmp

    # Returns True if file match report condition
    def matchCondition(self, file):
        result = self.multiCondition == "and"  # if or, false by default and became True on first match found
        # if and, true by default and became False on 1st unmatch

        for tag in self.tags:
            if file.hasTagStartingBy(tag):
                if self.multiCondition != "and":
                    result = True
                    break
            elif self.multiCondition == "and":
                result = False
                break

        for path in self.paths:
            if file.pathMatch(path):
                if self.multiCondition != "and":
                    result = True
                    break
            elif self.multiCondition == "and":
                result = False
                break

        return result

    def title(self):
        return self.json["title"]

    @staticmethod
    def mappingTags(tags, allTags):
        result = []
        for token in tags:
            token = "#{}".format(token)
            for tag in allTags:
                if tag.startswith(token) and not tag.endswith("/"):
                    result.append(tag)
        return result

    def getContents(self):
        try:
            return self.json["contents"]
        except KeyError:
            try:
                ref = self.json["content_ref"]
                try:
                    return self.allSubContents[ref]
                except KeyError:
                    raise UnknownContentRef(ref, self.json)
            except KeyError:
                return None

    def getCount(self):
        try:
            return self.json["count"]
        except KeyError:
            return None

    def generate(self, writer):
        if self.isVirtual:
            logging.debug("MDR |  | {} VIRTUAL [{}->{}] ({} {})".format(LONG_BLANK[0:len(self.level) * 2],
                                                           len(self.inputFiles), len(self.filteredFiles), self.tags,
                                                           self.paths))
            if len(self.filteredFiles) > 0:
                # virtual content that must be expanded !
                for tag in sorted(self.mappingTags(self.tags, self.allTags)):
                    content = self.json.copy()
                    del content["else"]
                    content["title"] = tag[len(self.tags[0]) + 1:]  # Replace %TAGNAME% title by expended tag detected
                    content["tag_condition"] = [tag[1:]]  # and use the expanded tag to filer
                    if len(content["title"]) > 0:
                        MhReportEntry(content, self.filteredFiles.copy(), self.allTags,
                                      self.allSubContents, self.commentTag, self.showTags, self.labels, self.level).generate(writer)
            # Proceed to else of VIRTUAL block
            try:
                MhReportEntry(self.json["else"], self.elseFiles, self.allTags,
                              self.allSubContents, self.commentTag, self.showTags, self.labels, self.level).generate(writer)
            except KeyError:
                pass

            return

        logging.debug("MDR |  | {} {} [{}->{} / {}] ({} {})".format(LONG_BLANK[0:len(self.level) * 2], self.title(),
                                                       len(self.inputFiles), len(self.filteredFiles),
                                                       len(self.elseFiles), self.tags, self.paths))

        nextLevel = "{}#".format(self.level)
        if len(self.filteredFiles) > 0:
            writer.writelines("{} {} ({})\n".format(self.level, self.title(), len(self.filteredFiles)))
            titleToGenerate = True

            json_contents = self.getContents()
            if json_contents is not None:
                files = self.filteredFiles
                for content in json_contents:
                    cr = MhReportEntry(content, files, self.allTags, self.allSubContents,
                                       self.commentTag, self.showTags, self.labels, nextLevel)
                    cr.generate(writer)
                    files = cr.elseFiles
            else:
                json_count = self.getCount()
                if json_count is not None:
                    writer.writelines("|What|Count|\n|-|-|")
                    for key, value in json_count.items():
                        writer.writelines("\n| {} | {} |".format(key, MhCountEntry(value, self.filteredFiles).getCount()))
                else:
                    for name, file in self.filteredFiles.items():
                        comment = ""
                        if self.commentTag is not None:
                            comments = file.getTagComment(self.commentTag)
                            if comments is not None:
                                for val in comments:
                                    if val is not None:
                                        comment = comment + " <font size=-1>{}</font><br>".format(val.strip())
                        ctags = ""
                        if self.showTags is not None:
                            for showTag in self.showTags:
                                for tag in file.getTagStartingBy(showTag):
                                    stag = tag[2 + len(showTag):]
                                    if len(stag) > 0:
                                        ctags = "{} ``{}``".format(ctags, stag)
                        # Main line with entry found data
                        #                    writer.writelines("- [[{}]] {} {} \n".format(name, ctags, comment))
                        if self.commentTag is not None and titleToGenerate:
                            writer.writelines("|{}|{}|{}|\n".format(self.labels.about, self.labels.tags, self.labels.comment))
                            writer.writelines("|----|----|-------|\n")
                            titleToGenerate = False
                        if self.commentTag is not None:
                            writer.writelines("| [[{}]] | {} | {} |\n".format(name, ctags, comment))
                        else:
                            writer.writelines("[[{}]]  {} \n".format(name, ctags))

            try:
                MhReportEntry(self.json["else"], self.elseFiles, self.allTags,
                              self.allSubContents, self.commentTag, self.showTags, self.labels, nextLevel).generate(writer)
            except KeyError:
                pass


class MhReport:

    def __init__(self, json, baseFolder, inputFiles, allTags, allSubContents):
        self.json = json
        self.baseFolder = baseFolder
        self.inputFiles = inputFiles
        self.allTags = allTags
        self.allSubContents = allSubContents

        # Setup comment tag
        try:
            self.commentTag = self.json["commentTag"]
        except KeyError:
            self.commentTag = None

        # Setup show tags
        try:
            self.showTags = self.json["showTags"]
        except KeyError:
            self.showTags = None

    def target(self):
        return self.baseFolder + '/' + self.json["target"]

    def generate(self):
        rootReport = MhReportEntry(self.json, self.inputFiles, self.allTags, self.allSubContents,
                                   self.commentTag, self.showTags)
        logging.info("MDR | Generate report \"{}\" to {}".format(rootReport.title(), self.target()))
        with open(self.target(), 'w', encoding='utf-8') as writer:
            rootReport.generate(writer)
