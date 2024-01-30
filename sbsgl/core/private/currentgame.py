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

# TODO Use GameProcessHolder in gui instead of process : line 147 ( proc, gui.py )
from sbsgl.log import Log


class GameProcessHolder:

    def __init__(self, proc=None):
        if proc is None:
            self.pid = 0
            self.process = None
        else:
            self.pid = proc.pid
            self.process = proc.process

    # Started does not mean still running
    def isSet(self):
        return self.pid != 0

    def setProcess(self, process):
        self.pid = process.getPid()
        self.process = process

    def reset(self):
        self.pid = 0
        self.process = None
        Log.debug("CURRENT GAME: reset selection")

    def getName(self):
        if self.process is not None:
            return self.process.getName()
