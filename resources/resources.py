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
    SPLASH = None
    APP = None
    ABOUT = None
    HOME = None
    HOME_TAB = None
    FOLDER = None
    USER = None
    PENCIL = None
    QUESTION = None
    START = None
    EXIT = None
    REFRESH = None
    REPORT = None
    IMPORT = None
    SMALL_DOCUMENT = None
    DOCUMENT = None
    CLEAR = None
    OK = None
    KO = None
    HOURGLASS = None
    STORY1 = None
    STORY2 = None
    OBSIDIAN = None
    POPMENU = None
    VOID = None
    PLAY = None
    RUNNING = None
    MANY = None
    NOT_FOUND = None
    SAVE = None
    EXPAND = None
    PLUS = None
    MINUS = None
    DELETE = None
    UP = None
    DOWN = None

    CACHE = dict()

    @staticmethod
    def initIcons():
        Icons.SPLASH = QPixmap(resource_path("splash.png"))
        Icons.APP = QPixmap(resource_path("home.png"))
        Icons.ABOUT = QPixmap(resource_path("about-24.png"))
        Icons.HOME = QPixmap(resource_path("home.png"))
        Icons.HOME_TAB = QPixmap(resource_path("homeV.png"))
        Icons.FOLDER = QPixmap(resource_path("file-explorer-16.png"))
        Icons.USER = QPixmap(resource_path("user.png"))
        Icons.PENCIL = QPixmap(resource_path("pencil.png"))
        Icons.QUESTION = QPixmap(resource_path("question-mark-16.png"))
        Icons.START = QPixmap(resource_path("start.png"))
        Icons.EXIT = QPixmap(resource_path("power-off-24.png"))
        Icons.REFRESH = QPixmap(resource_path("refresh-16.png"))
        Icons.SMALL_DOCUMENT = QPixmap(resource_path("document-16.png"))
        Icons.DOCUMENT = QPixmap(resource_path("document.png"))
        Icons.CLEAR = QPixmap(resource_path("clear.png"))
        Icons.OK = QPixmap(resource_path("check-16.png"))
        Icons.KO = QPixmap(resource_path("error-16.png"))
        Icons.HOURGLASS = QPixmap(resource_path("hourglass.png"))
        Icons.STORY1 = QPixmap(resource_path("story1-16.png"))
        Icons.STORY2 = QPixmap(resource_path("story2-16.png"))
        Icons.OBSIDIAN = QPixmap(resource_path("obsidian.png"))
        Icons.POPMENU = QPixmap(resource_path("menu-16.png"))
        Icons.VOID = QPixmap(resource_path("void-16.png"))
        Icons.PLAY = QPixmap(resource_path("play-16.png"))
        Icons.RUNNING = QPixmap(resource_path("void-16.png"))
        Icons.REPORT = QPixmap(resource_path("report-24.png"))
        Icons.IMPORT = QPixmap(resource_path("import-file-24.png"))
        Icons.MANY = QPixmap(resource_path("many-16.png"))
        Icons.NOT_FOUND = QPixmap(resource_path("clear-search-16.png"))
        Icons.SAVE = QPixmap(resource_path("save-16.png"))
        Icons.EXPAND = QPixmap(resource_path("expand-16.png"))
        Icons.PLUS = QPixmap(resource_path("plus-16.png"))
        Icons.MINUS = QPixmap(resource_path("minus-16.png"))
        Icons.DELETE = QPixmap(resource_path("delete-16.png"))
        Icons.UP = QPixmap(resource_path("up-16.png"))
        Icons.DOWN = QPixmap(resource_path("down-16.png"))

    @staticmethod
    def loadIcons(iconName):
        try:
            return Icons.CACHE[iconName]
        except KeyError:
            icon = QPixmap(resource_path("{}.png".format(iconName)))
            Icons.CACHE[iconName] = icon
            return icon
