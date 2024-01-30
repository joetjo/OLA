from sbsgl.jopsetup import JopSetup

# True for print_mode
JopSETUP = JopSetup(False)


class JopLauncher:
    # To be updated on release
    VERSION = '2023.12.12a'
    DEBUG = False
    ###########################
    APP_NAME = 'Jop Game Launcher'
    ABOUT = "SbSGL\nThe Simple but Smart Game Launcher\nOld School GUI\n[No login/No internet access]"
    SHORT_ABOUT = "JoProd@2023 by joetjo@Github"
    URL = "https://github.com/joetjo/jopLauncher"
    ICON_URL = "https://icons8.com"

    DB_VERSION = 4

    GAME_PLATFORMS = {
        "steam.exe": JopSETUP.STEAM,
        "GalaxyClient.exe": JopSETUP.GOG,
        "EpicGamesLauncher.exe": JopSETUP.EPIC,
        "upc.exe": JopSETUP.UBISOFT,
        "itch.exe": JopSETUP.ITCHIO,
        "Origin.exe": JopSETUP.ORIGIN
    }

    COM_APP_DISCORD = "Discord"
    COM_APP = {
        "Discord.exe": COM_APP_DISCORD
    }

    EXEC_FILE = [("Executable", "*.exe"),
                 ("Batch file", "*.bat")]

    NOTE_FILE = [("Markdown", "*.md"),
                 ("Text", "*.txt"),
                 ("whatever you want", "*.*")]
