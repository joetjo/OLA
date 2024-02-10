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

import os
import string
from pathlib import Path
from tkinter import filedialog

VALID_CHARS_4_FILENAME = "-_.() {}{}".format(string.ascii_letters, string.digits)


class GhFileUtil:

    @staticmethod
    def normalizeFileName(file):
        return ''.join(c for c in file if c in VALID_CHARS_4_FILENAME)

    @staticmethod
    def fileExist(file):
        return Path(file).is_file()

    @staticmethod
    def folderExist(file):
        return Path(file).is_dir()

    @staticmethod
    def home():
        return str(Path.home())

    @staticmethod
    def basenameWithExtent(file):
        return Path(file).stem

    @staticmethod
    def parentFolder(file):
        path = Path(file)
        return path.parent.absolute()

    @staticmethod
    def fileSelection(initialdir=os.getcwd(),
                      title="Select file",
                      filetypes=[("Text Files", "*.txt")]):
        return filedialog.askopenfilename(initialdir=initialdir, title=title, filetypes=filetypes)

    @staticmethod
    def findFileInFolder(name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)
