
import logging
import sys

from config import OLASetup
from gui import OLAApplication

print("Obsidian Launcher Assistant - logging initialized (log file: {})".format(OLASetup.LOG_FILENAME))
app = OLAApplication(sys.argv)

logging.info("OLAApplication - starting application execution")
app.start()
logging.info("OLAApplication - application terminated")

