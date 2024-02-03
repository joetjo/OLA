from pathlib import Path
import sys

from PySide6.QtGui import QPixmap

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    DEVIL_BUNDLE_DIR = Path(sys._MEIPASS)
else:
    DEVIL_BUNDLE_DIR = Path(__file__).parent.parent


def resource_path(res):
    """
    resource loading compatible with pyinstaller "one file" package.
    """
    return "{}/res/{}".format(DEVIL_BUNDLE_DIR, res)


class Icons:
    """to be initialized in gui.application.py initIcons()"""
    APP = None
    HOME = None
    HOME_TAB = None
    FOLDER = None
    USER = None
    PENCIL = None
    QUESTION = None
    START = None
    EXIT = None
    REFRESH = None
    SMALL_DOCUMENT = None
    DOCUMENT = None
    CLEAR = None
    OK = None
    KO = None
    HOURGLASS = None
    OBSIDIAN = None
    POPMENU = None
    VOID = None
    PLAY = None
    RUNNING = None

    @staticmethod
    def initIcons():
        Icons.APP = QPixmap(resource_path("home.png"))
        Icons.HOME = QPixmap(resource_path("home.png"))
        Icons.HOME_TAB = QPixmap(resource_path("homeV.png"))
        Icons.FOLDER = QPixmap(resource_path("file-explorer-16.png"))
        Icons.USER = QPixmap(resource_path("user.png"))
        Icons.PENCIL = QPixmap(resource_path("pencil.png"))
        Icons.QUESTION = QPixmap(resource_path("question.png"))
        Icons.START = QPixmap(resource_path("start.png"))
        Icons.EXIT = QPixmap(resource_path("close-16.png"))
        Icons.REFRESH = QPixmap(resource_path("refresh-16.png"))
        Icons.SMALL_DOCUMENT = QPixmap(resource_path("document-16.png"))
        Icons.DOCUMENT = QPixmap(resource_path("document.png"))
        Icons.CLEAR = QPixmap(resource_path("clear.png"))
        Icons.OK = QPixmap(resource_path("ok.png"))
        Icons.KO = QPixmap(resource_path("ko.png"))
        Icons.HOURGLASS = QPixmap(resource_path("hourglass.png"))
        Icons.OBSIDIAN = QPixmap(resource_path("obsidian.png"))
        Icons.POPMENU = QPixmap(resource_path("menu-16.png"))
        Icons.VOID = QPixmap(resource_path("void-16.png"))
        Icons.PLAY = QPixmap(resource_path("play-16.png"))
        Icons.RUNNING = QPixmap(resource_path("void-16.png"))
