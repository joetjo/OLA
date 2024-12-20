from sbsgl.sbsglsetup import SbSGLSetup

# True for print_mode
SbSGLSETUP = SbSGLSetup(False)


class SbSGLLauncher:
    DEBUG = False
    DB_VERSION = 4

    GAME_PLATFORMS = {
        "steam.exe": SbSGLSETUP.STEAM,
        "GalaxyClient.exe": SbSGLSETUP.GOG,
        "EpicGamesLauncher.exe": SbSGLSETUP.EPIC,
        "upc.exe": SbSGLSETUP.UBISOFT,
        "itch.exe": SbSGLSETUP.ITCHIO,
        "Origin.exe": SbSGLSETUP.ORIGIN
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
