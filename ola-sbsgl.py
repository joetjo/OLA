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
from pathlib import Path

# KEEP UNUSED IMPORT FOR pyInstaller !
from PySide6.QtCore import QCoreApplication, QSize, QThreadPool, QTimer, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QLabel, QMainWindow, \
    QVBoxLayout, \
    QApplication, QStatusBar, QGroupBox, QLineEdit, QGridLayout, QPushButton, QInputDialog, QComboBox, QMenu, QMessageBox, QCheckBox, QScrollArea, QSplashScreen, QTextBrowser, QDialog

from ola.gui import OLAApplication, OLAVersionInfo, OLAGuiSetup

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    OLAGuiSetup.OLA_DEV_MODE = False
    print("Starting in packaged mode (temp folder {})".format(Path(sys._MEIPASS)))

stdout = logging.StreamHandler(stream=sys.stdout)
fmt = logging.Formatter("%(asctime)s %(message)s")
stdout.setFormatter(fmt)

logger = logging.getLogger()
# Remove stderr, default handler from logger
logger.removeHandler(logger.handlers[0])

logger.setLevel(logging.INFO)
logger.addHandler(stdout)
logging.info("OLAApplication - starting application execution")

print("OLA Loggers setup:")
for handler in logger.handlers:
    print(handler)

app = OLAApplication(sys.argv, OLAVersionInfo.VERSION)
app.start()
logging.info("OLAApplication - application terminated")