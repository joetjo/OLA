# Copyright 2024 joetjo https://github.com/joetjo/MarkdownHelper
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

import psutil

# All call to psutil is done here in order to be able to test without a real call
from launcher.log import Log


class ProcessUtil:

    def process_iter(self):
        return psutil.process_iter()

    def readProcessAttributes(self, process):
        try:
            return process.as_dict(attrs=['pid', 'name', 'exe'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            Log.info("--- unable to access process ---" + e)
            return None
