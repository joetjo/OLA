# Copyright 2024 joetjo https://github.com/joetjo/OLA
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
import sys

from config import OLASetup
from gui import OLAApplication

print("Obsidian Launcher Assistant - logging initialized (log file: {})".format(OLASetup.LOG_FILENAME))
app = OLAApplication(sys.argv)

logging.info("OLAApplication - starting application execution")
app.start()
logging.info("OLAApplication - application terminated")

