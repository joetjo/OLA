
import logging
from version import OLAVersionInfo


class OLASetup:
    LOG_LEVEL = logging.INFO
    LOG_FILENAME = "ola.log"


logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', filename=OLASetup.LOG_FILENAME, filemode='w', level=OLASetup.LOG_LEVEL)
logging.info("Obsidian Launcher Assistant %s", OLAVersionInfo.CURRENT)