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
from version import OLAVersionInfo


class OLASetup:
    LOG_LEVEL = logging.DEBUG
    LOG_FILENAME = "ola.log"


logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', filename=OLASetup.LOG_FILENAME, filemode='w', level=OLASetup.LOG_LEVEL)
logging.info("Obsidian Launcher Assistant %s", OLAVersionInfo.CURRENT)