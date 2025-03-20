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

from base.fileutil import GhFileUtil
# Ugly but simple
from markdownHelper.label import MhLabels

LONG_BLANK = "                                                                                                         "

ALLOWED_ATTRIBUTES = ["target",  # 1st level only: target file path
                      "title",  # mandatory on each bloc
                      "about",
                      "group",
                      "tag_condition",  # optional: tag list to filter content ( can be tag prefix )
                      "tag_refs",  # optional : references by name to tag list in shared data
                      "path_condition",  # optional: name list that should be used in folder path
                      "path_ref",  # reference by name to a path condition in shared data
                      "condition_type",  # if "not" --> inverse the tag_condition or path condition
                      "multi_condition",  # "or" by default. can be set to "and"
                      "contents",  # sub blocs / in not defined --> leaf to print
                      "count",  # sub blocs / statistic bloc
                      "content_ref",  # reference to a "shared content definition" under shared_contents node
                      "else",  # optional: bloc to process all entries not selected by filter
                      "commentTag",  # a comment TAG is a tag that start at the beginning of the line and
                      # the text on the same line will be registered as a comment and shown in report.
                      "showTags",  # ref to tag list to show (tag that start by the requested string will be added to the line)
                      ]


class UnknownJSonAttribute(Exception):
    def __init__(self, attName, json,
                 message="Unknown JSon attribute \"{}\" used in report, allowed attributes are: {}, json bloc:\n{}"):
        self.message = message
        super().__init__(self.message.format(attName, ALLOWED_ATTRIBUTES, json))


class UnknownPathRef(Exception):
    def __init__(self, ref, json,
                 message="Unknown path reference \"{}\" used, json bloc:\n{}"):
        self.message = message
        super().__init__(self.message.format(ref, json))


class UnknownTagRefs(Exception):
    def __init__(self, ref, json,
                 message="Unknown tags reference \"{}\" used, json bloc:\n{}"):
        self.message = message
        super().__init__(self.message.format(ref, json))


class UnknownInfoTafRef(Exception):
    def __init__(self, ref, json,
                 message="Unknown info tags reference \"{}\" used, json bloc:\n{}"):
        self.message = message
        super().__init__(self.message.format(ref, json))


class UnknownContentRef(Exception):
    def __init__(self, ref, json,
                 message="Unknown content reference \"{}\" used, json bloc:\n{}"):
        self.message = message
        super().__init__(self.message.format(ref, json))


class ReferenceUtil:

    @staticmethod
    def getPath(json, allSubContents):
        try:
            return json["path_condition"]
        except KeyError:
            try:
                ref = json["path_ref"]
                try:
                    return allSubContents["paths"][ref]
                except KeyError:
                    raise UnknownPathRef(ref, allSubContents["paths"])
            except KeyError:
                return []

    @staticmethod
    def getTags(json, allSubContents):
        try:
            return json["tag_condition"]
        except KeyError:
            try:
                refs = json["tag_refs"]
                result = []
                for ref in refs:
                    try:
                        tags = allSubContents["tags"][ref]
                        for tag in tags:
                            result.append(tag)
                    except KeyError:
                        raise UnknownTagRefs(refs, allSubContents["tags"])
                return result
            except KeyError:
                return []

    @staticmethod
    def showTags(json, allSubContents):
        try:
            ref = json["showTags"]
            try:
                return allSubContents["info_tags"][ref]
            except KeyError:
                raise UnknownInfoTafRef(ref, allSubContents["paths"])
        except KeyError:
            return []


class MhReportDescriptionSheet:
    def __init__(self, title, reportLink):
        self.reportLink = reportLink
        self.lines = [title]
        self.lines.append("\n| Sheet | Filtering |\n")
        self.lines.append("|-|-|\n")

    @staticmethod
    def valuesToConditionStr(separator, values):
        empty = True
        condition = ""
        for val in values:
            if not empty:
                condition = "{}{}``{}``".format(condition, separator, val)
            else:
                condition = "{} ``{}``".format(condition, val)
                empty = False
        return condition

    def addTarget(self, title, name, commentTag):
        self.lines.append("| {} : [[{}]] | comment tag: {} |\n".format(title, name, commentTag))

    def addExpandBy(self, tags):
        self.lines.append("| | > Expand by tag {} | \n".format(tags))

    def addFiltering(self, tags, paths, isNot, isAnd):
        logOperator = " **OR** "
        if isAnd == "and":
            logOperator = " **AND** "
        notOperator = ""
        if len(isNot) > 0:
            notOperator = " **NOT** "
        hasTags = tags is not None and len(tags) > 0
        hasPaths = paths is not None and len(paths) > 0
        condition = ""
        if hasTags:
            condition = "*tags* ( {} )".format(MhReportDescriptionSheet.valuesToConditionStr(logOperator, tags))
        if hasPaths:
            if hasTags:
                condition = "{}{}*Paths* ( {} )".format(condition, logOperator, MhReportDescriptionSheet.valuesToConditionStr(logOperator, paths))
            else:
                condition = "*Paths* ( {} )".format(MhReportDescriptionSheet.valuesToConditionStr(logOperator, paths))
        if len(condition) > 0:
            self.lines.append("| | {}{} |\n".format(notOperator, condition))


class MhEntry:
    def __init__(self, json, inputFiles, allSubContents):
        self.json = json
        self.inputFiles = inputFiles
        self.allSubContents = allSubContents

        for key in json:
            if key not in ALLOWED_ATTRIBUTES:
                raise UnknownJSonAttribute(key, json)

        # Setup content filter
        self.tags = ReferenceUtil.getTags(json, allSubContents)
        self.paths = ReferenceUtil.getPath(self.json, allSubContents)

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


class MhCountEntry(MhEntry):

    def __init__(self, json, inputFiles, allSubContents):

        super().__init__(json, inputFiles, allSubContents)
        self.count = 0

        for name, file in self.inputFiles.items():
            if self.matchCondition(file):
                self.count = self.count + 1

    def getCount(self):
        return self.count


class MhReportEntry(MhEntry):

    # inputFiles: dict of name, MhMarkdownFiles
    def __init__(self, json, inputFiles, allTags, allSubContents, reportSheet, commentTag, showTags, parentTitle, labels=None, level="#", isRoot=False):
        super().__init__(json, inputFiles, allSubContents)
        self.level = level
        self.allTags = allTags
        self.reportSheet = reportSheet
        self.commentTag = commentTag
        self.showTags = showTags
        if labels is None:
            self.labels = MhLabels(json)
        else:
            self.labels = labels

        self.isFiltering = not len(self.tags) == 0 or not len(self.paths) == 0
        self.isVirtual = self.title() == "%TAGNAME%"
        self.isRoot = isRoot
        if self.isRoot:
            self.paragraphTitle = ""
        elif not self.isVirtual:
            if parentTitle is not None and len(parentTitle)> 0:
                self.paragraphTitle = "{} - {}".format(parentTitle, self.title())
            else:
                self.paragraphTitle = self.title()
        else:
            self.paragraphTitle = parentTitle

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

        self.lineGenerated = 0

    def title(self):
        try:
            return self.json["title"]
        except KeyError:
            return ""

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
                if self.reportSheet is not None:
                    self.reportSheet.addExpandBy(self.tags)
                for tag in sorted(self.mappingTags(self.tags, self.allTags)):
                    content = self.json.copy()
                    del content["else"]
                    content["title"] = GhFileUtil.ConvertUpperCaseWordSeparatedNameToStr(tag[len(self.tags[0]) + 1:])  # Replace %TAGNAME% title by expended tag detected
                    content["tag_condition"] = [tag[1:]]  # and use the expanded tag to filer
                    if len(content["title"]) > 0:
                        self.lineGenerated = self.lineGenerated + MhReportEntry(content, self.filteredFiles.copy(), self.allTags,
                                      self.allSubContents, None, self.commentTag, self.showTags, self.paragraphTitle, self.labels, self.level).generate(writer)
            # Proceed to else of VIRTUAL block
            try:
                self.lineGenerated = self.lineGenerated + MhReportEntry(self.json["else"], self.elseFiles, self.allTags,
                              self.allSubContents, self.reportSheet, self.commentTag, self.showTags, self.paragraphTitle, self.labels, self.level).generate(writer)
            except KeyError:
                pass

            return self.lineGenerated

        logging.debug("MDR |  | {} {} [in:{}->match:{}/else:{}] ( {} {} tags:{} / paths:{})".format(LONG_BLANK[0:len(self.level) * 2], self.paragraphTitle,
                                                                    len(self.inputFiles), len(self.filteredFiles),
                                                                    len(self.elseFiles), self.inverseCondition, self.multiCondition,
                                                                    self.tags, self.paths))

        nextLevel = self.level
        if len(self.filteredFiles) > 0:
            currentTitle = "{} {} ({})\n".format(self.level, self.paragraphTitle, len(self.filteredFiles))
            # writer.writelines(currentTitle)  # this display a title for each hierarchy to the report, lot of titles
            if self.reportSheet is not None:
                self.reportSheet.addFiltering(self.tags, self.paths, self.inverseCondition, self.multiCondition)
            titleToGenerate = True

            json_contents = self.getContents()
            if json_contents is not None:
                files = self.filteredFiles
                for content in json_contents:
                    cr = MhReportEntry(content, files, self.allTags, self.allSubContents, self.reportSheet,
                                       self.commentTag, self.showTags, self.paragraphTitle, self.labels, nextLevel)
                    self.lineGenerated = self.lineGenerated + cr.generate(writer)
                    files = cr.elseFiles
            else:
                json_count = self.getCount()
                if json_count is not None:
                    writer.writelines("|What|Count|\n|-|-|")
                    for key, value in json_count.items():
                        writer.writelines("\n| {} | {} |".format(key, MhCountEntry(value, self.filteredFiles, self.allSubContents).getCount()))
                        self.lineGenerated = self.lineGenerated + 1
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
                            nextLevel = "{}#".format(self.level)
                            writer.writelines(currentTitle)
                            writer.writelines("|{}|{}|{}|\n".format(self.labels.about, self.labels.tags, self.labels.comment))
                            writer.writelines("|----|----|-------|\n")
                            titleToGenerate = False
                        if self.commentTag is not None:
                            writer.writelines("| [[{}]] | {} | {} |\n".format(name, ctags, comment))
                        else:
                            writer.writelines("[[{}]]  {} \n".format(name, ctags))
                        self.lineGenerated = self.lineGenerated + 1

        if len(self.elseFiles) > 0:
            try:
                self.lineGenerated = self.lineGenerated + MhReportEntry(self.json["else"], self.elseFiles, self.allTags,
                              self.allSubContents, self.reportSheet, self.commentTag, self.showTags, "",
                              self.labels, nextLevel).generate(writer)
            except KeyError:
                pass
        return self.lineGenerated

class MhReport:

    def __init__(self, json, baseFolder, inputFiles, allTags, allSubContents, reportSheet):
        self.json = json
        self.baseFolder = baseFolder
        self.inputFiles = inputFiles
        self.allTags = allTags
        self.allSubContents = allSubContents
        self.reportSheet = reportSheet

        # Setup comment tag
        try:
            self.commentTag = self.json["commentTag"]
        except KeyError:
            self.commentTag = None

        # Setup show tags
        self.showTags = ReferenceUtil.showTags(self.json, allSubContents)

    def target(self):
        return self.baseFolder + '/' + self.json["target"]

    def generate(self):
        rootReport = MhReportEntry(self.json, self.inputFiles, self.allTags, self.allSubContents, self.reportSheet,
                                   self.commentTag, self.showTags, "", isRoot=True)
        logging.info("MDR | Generate report \"{}\" to {}".format(self.json["title"], self.target()))
        with open(self.target(), 'w', encoding='utf-8') as writer:
            writer.writelines(
                "> *Markdown generated report by [joetjo](https://github.com/joetjo/OLA) - do not edit* - see [[{}]] for description\n\n".format(
                    self.reportSheet.reportLink[0:len(self.reportSheet.reportLink) - 3]))  # adding an empty line at the beginning avoid having the title selected when selecting the sheet
            try:
                about = self.json["about"]
                writer.writelines("*CONTENT*\n```")
                writer.writelines(about)
                writer.writelines("```\n")
            except KeyError:
                pass  # no about set
            lineDisplayedCount = rootReport.generate(writer)
            writer.writelines("\n")
            writer.writelines("----\n")
            writer.writelines("# Entries: {}\n".format(lineDisplayedCount))
