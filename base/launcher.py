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
import subprocess
import threading


class GhLauncher:

    @staticmethod
    def launch(label, exe, cwd=os.getcwd()):
        print("Launcher: Launching {} ({}) from folder {} ".format(label, exe, cwd))
        bg = threading.Thread(target=GhLauncher.launchImpl, args=(exe, cwd))
        bg.start()

    @staticmethod
    def launchImpl(exe, cwd):
        subprocess.run(exe, cwd=cwd)
