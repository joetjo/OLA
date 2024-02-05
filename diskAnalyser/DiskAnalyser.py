import logging
import os
from datetime import datetime

from base.setup import GhSetup


class GhDiskStat:
    def __init__(self, name):
        self.name = name
        self.folderCount = 0
        self.fileCount = 0
        self.size = 0

    def write(self, writer):
        writer.writelines(" - ```{}```: Folders: {}, Files: {} \n".format(self.name, self.folderCount, self.fileCount))


class GhDiskEntries:
    def __init__(self, name):
        self.name = name
        self.names = None
        self.leafNames = None
        self.entries = dict()  # key file or folder name, value : list of location
        self.entriesLC = dict()
        self.entriesCharOnly = dict()
        self.duplicateByCase = dict()  # name lower case, value : list of names with same lower case
        self.duplicateByCharOnly = dict()  # name with only meaning full character, value : list of names with same lower case
        self.leafEntries = dict()
        self.dupCount = 0

    def addPath(self, rootFolder, path, isLeaf, ignore):  # absolute path
        base = os.path.dirname(path)
        name = os.path.basename(path)
        folderName = path[len(rootFolder) + 1:]
        self.addPathAndName(base, name, ignore)
        if len(folderName) > 0 and isLeaf:
            try:
                self.leafEntries[folderName].append(path)
            except KeyError:
                self.leafEntries[folderName] = [path]

    def addPathAndName(self, path, name, ignore):  # absolute path
        logging.debug("FUR |  [{}] Location:[{}] Name:[{}]".format(self.name, path, name))
        if name not in ignore:
            try:
                self.entries[name].append(path)
            except KeyError:
                self.entries[name] = [path]

            nameLowerCase = name.lower()
            try:
                self.entriesLC[nameLowerCase].append(path)
            except KeyError:
                self.entriesLC[nameLowerCase] = [path]
            try:
                self.duplicateByCase[nameLowerCase].append(name)
            except KeyError:
                self.duplicateByCase[nameLowerCase] = [name]

            nameCharOnly = ''.join(x for x in name if x.isalpha() or x.isdigit())
            try:
                self.entriesCharOnly[nameCharOnly].append(path)
            except KeyError:
                self.entriesCharOnly[nameCharOnly] = [path]
            try:
                self.duplicateByCharOnly[nameCharOnly].append(name)
            except KeyError:
                self.duplicateByCharOnly[nameCharOnly] = [name]

    def sort(self):
        self.names = sorted(self.entries)
        self.leafNames = sorted(self.leafEntries)

    def writeLeaf(self, writer, ignore):
        for name in self.leafNames:
            if name not in ignore:
                for location in self.leafEntries[name]:
                    writer.writelines(" - [[{}]] : [```{}```](<{}>)\n".format(name, name, location.replace("\\", "/")))

    def write(self, writer, ignore):
        for name in self.names:
            if len(self.entries[name]) > 1:
                if name not in ignore:
                    self.dupCount = self.dupCount + 1
                    writer.writelines(" - Entry: ```{}``` \n".format(name))
                    for location in self.entries[name]:
                        writer.writelines("        |   [```{}```](<{}>)\n".format(location, location.replace("\\", "/")))
                    writer.writelines("\n".format(name))

        dupCaseLC = 0
        for name in self.duplicateByCase:
            if len(self.duplicateByCase[name]) > 1:
                dupCaseLC = dupCaseLC + 1

        if dupCaseLC > 0:
            writer.writelines("\n----\n{} Duplicate(s) {} name(s) with different case".format(dupCaseLC, self.name))
            for name in self.duplicateByCase:
                if len(self.duplicateByCase[name]) > 1:
                    writer.writelines("\n - {} : ".format(name))
                    for name2 in self.duplicateByCase[name]:
                        location = self.entries[name2][0].replace("\\", "/")
                        writer.writelines(" [```{}```](<{}>)  ".format(name2, location))
            writer.writelines("\n----\n")

        dupCaseCO = 0
        for name in self.duplicateByCharOnly:
            if len(self.duplicateByCharOnly[name]) > 1:
                dupCaseCO = dupCaseCO + 1

        if dupCaseCO > 0:
            writer.writelines("\n----\n{} Duplicate(s) {} name(s) when checking only normal characters".format(dupCaseCO, self.name))
            for name in self.duplicateByCharOnly:
                if len(self.duplicateByCharOnly[name]) > 1:
                    writer.writelines("\n - {} : ".format(name))
                    for name2 in self.duplicateByCharOnly[name]:
                        location = self.entries[name2][0].replace("\\", "/")
                        writer.writelines(" [```{}```](<{}>)  ".format(name2, location))
            writer.writelines("\n----\n")

    def writeSuspicious(self, writer, suspiciousSuffix):
        writer.writelines("\n----\n# Suspicious uncompressed files\n\n")
        count = 0
        for name in self.entries:
            suspicious = False
            for suffix in suspiciousSuffix:
                if name.endswith(suffix):
                    suspicious = True
            if suspicious:
                count = count + 1
                writer.writelines(" - Entry: ```{}``` \n".format(name))
                for location in self.entries[name]:
                    writer.writelines("        |   [```{}```](<{}>)\n".format(location, location.replace("\\", "/")))

        writer.writelines("\n----\n")
        return count


class DiskAnalyser:
    def __init__(self):
        self.SETUP = GhSetup('markdownHelper')
        self.VAULT = self.SETUP.getBloc("global")["base_folder"]
        self.FOLDERS = self.SETUP.getBloc("disk")["folders"]
        self.IGNORE_DUPLICATE = self.SETUP.getBloc("disk")["ignoreDuplicateOn"]
        self.SUSPICIOUS_SUFFIX = self.SETUP.getBloc("disk")["suffixToCheck"]
        self.REPORT_ALLFILES = "{}\\{}".format(self.VAULT, self.SETUP.getBloc("disk")["targetAll"])
        self.REPORT_ERRORS = "{}\\{}".format(self.VAULT, self.SETUP.getBloc("disk")["targetErrors"])
        self.globalStat = GhDiskStat("global")
        self.stats = []
        self.allFiles = GhDiskEntries("files")
        self.allFolders = GhDiskEntries("folders")
        self.unsortedFiles = dict()  # key root folder, value : list of files

    def generateReport(self):
        logging.info("FUR | Markdown vault: {}".format(self.REPORT_ALLFILES))
        logging.info("FUR | Folder to check: {}".format(self.REPORT_ERRORS))
        for folder in self.FOLDERS:
            logging.debug("FUR |   | - {}".format(folder))

        logging.debug("FUR | Parsing all requested folders....")
        for folder in self.FOLDERS:
            logging.debug("FUR |   | - {}".format(folder))
            stat = GhDiskStat(folder)
            self.unsortedFiles[folder] = []
            self.stats.append(stat)
            for root, dir, files in os.walk(folder):
                self.globalStat.folderCount = self.globalStat.folderCount + 1
                self.globalStat.fileCount = self.globalStat.fileCount + len(files)
                stat.folderCount = stat.folderCount + 1
                stat.fileCount = stat.fileCount + len(files)
                self.allFolders.addPath(folder, root, len(dir) == 0 or len(files) == 0, self.IGNORE_DUPLICATE)
                for file in files:
                    self.allFiles.addPathAndName(root, file, self.IGNORE_DUPLICATE)
                    if root == folder:
                        self.unsortedFiles[folder].append(file)
        self.allFiles.sort()
        self.allFolders.sort()

        logging.info("FUR | {} folders detected, {} files detected".format(self.globalStat.folderCount, self.globalStat.fileCount))
        logging.info("FUR | {} unique folders detected, {} unique files detected".format(len(self.allFolders.entries), len(self.allFiles.entries)))

        with open(self.REPORT_ALLFILES, 'w', encoding='utf-8') as writer:
            writer.writelines("> *Markdown generated report by [joetjo](https://github.com/joetjo/OLA) - do not edit*\n\n")  # adding an empty line at the beginning avoid having the title selected when selecting the sheet
            self.allFolders.writeLeaf(writer, self.IGNORE_DUPLICATE)

        with open(self.REPORT_ERRORS, 'w', encoding='utf-8') as writer:
            writer.writelines("> *Markdown generated report by [joetjo](https://github.com/joetjo/OLA) - do not edit*\n")  # adding an empty line at the beginning avoid having the title selected when selecting the sheet
            writer.writelines("\n> {} folders detected, {} files detected".format(self.globalStat.folderCount, self.globalStat.fileCount))
            writer.writelines("\n> {} unique folders detected, {} unique files detected".format(len(self.allFolders.entries), len(self.allFiles.entries)))

            writer.writelines("\n\nSome statistics:\n")
            self.globalStat.write(writer)
            writer.writelines("\nDetailed:\n")
            for stat in self.stats:
                stat.write(writer)

            writer.writelines("\n\n# Folders\n")
            self.allFolders.write(writer, self.IGNORE_DUPLICATE)
            writer.writelines("\n# Files\n")
            self.allFiles.write(writer, self.IGNORE_DUPLICATE)

            unsortedFileCount = 0
            writer.writelines("\n# Unsorted Files\n")
            for folder in self.unsortedFiles:
                if len(self.unsortedFiles[folder]) > 0:
                    writer.writelines("\n## {}\n".format(folder))
                    writer.writelines(">   [```{}```](<{}>)\n".format(folder, folder.replace("\\", "/")))
                    for file in self.unsortedFiles[folder]:
                        unsortedFileCount = unsortedFileCount + 1
                        writer.writelines("- {}\n".format(file))

            suspicious = self.allFiles.writeSuspicious(writer, self.SUSPICIOUS_SUFFIX)

            writer.writelines("\n> {} duplicated folder to check\n> {} duplicated files to check\n> {} unsorted files to check\n> {} suspicious files to check"
                              .format(self.allFolders.dupCount, self.allFiles.dupCount, unsortedFileCount, suspicious))
