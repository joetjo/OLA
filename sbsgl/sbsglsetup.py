# Copyright 2023 joetjo https://github.com/joetjo/MarkdownHelper
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

from base.setup import GhSetup

# Setup definition for ZikRandomizer
# Setup file is stored in home folder: .ZikMgr.json
# - FOLDER  # folder path on desktop/laptop
# - TARGET  # audio device folder path when mounted
# - BACKUP  # folder path on desktop/laptop where removed file are stored
# - EXTENT  # file extent to use
# - TAG  # prefix used to randomize file


class SbSGLSetup:
    _global_setup_ = None
    MAX_LAST_SESSION_COUNT = "MAX_LAST_SESSION_COUNT"
    GAME_PATTERN = "GAME_PATTERN"
    GAME_EXTENSION = "GAME_EXTENSION"
    NOTE_EXE = "NOTE_EXE"
    URL_EXE = "URL_EXE"
    LOCAL_FILE_FOLDER = "LOCAL_FILE_FOLDER"
    COMPANION_APP = "COMPANION_APP"
    MARKDOWN_REPORT = "MARKDOWN_REPORT"
    ICONFX_APP = "ICONFX_APP"
    DISCORD = "DISCORD"

    STEAM = "STEAM"
    GOG = "GOG"
    EPIC = "EPIC"
    UBISOFT = "UBISOFT"
    ITCHIO = "ITCHIO"
    ORIGIN = "ORIGIN"

    GAME_TYPES = "GAME_TYPES"
    GAME_STATUSES = "GAME_STATUSES"
    GAME_NOTES = "GAME_NOTES"

    EXTENDED_FILTER = "EXTENDED_FILTER"
    INSTALLED_MODE = "INSTALLED_MODE"
    EXTENDED_MODE = "EXTENDED_MODE"

    @staticmethod
    def SbSGLSetup():
        return SbSGLSetup._global_setup_

    def __init__(self, print_mode, content=None):
        self.print_mode = print_mode

        self.SETUP = GhSetup('SbSGL', content)

        self.SBSGL = self.SETUP.getBloc('SbSGL')

        self.dirty = False
        if print_mode:
            print("================= SbSGL SETUP  =========================")
        self.initSetupEntry(self.MAX_LAST_SESSION_COUNT, 30)
        self.initSetupEntry(self.GAME_PATTERN, 'jeux')
        self.initSetupEntry(self.GAME_EXTENSION, '.exe')
        self.initSetupEntry(self.NOTE_EXE, "C:/Program Files (x86)/Notepad++/notepad++.exe")
        self.initSetupEntry(self.URL_EXE, "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe")
        self.initSetupEntry(self.LOCAL_FILE_FOLDER, "C:/MarkdownFiles")
        self.initSetupEntry(self.COMPANION_APP, ["C:/Users/Machin/AppData/Local/Programs/Obsidian/Obsidian.exe"])
        self.initSetupEntry(self.MARKDOWN_REPORT, "True")
        self.initSetupEntry(self.ICONFX_APP, ["G:/NMPTF-PortableApps/PortableApps/IcoFXPortable/IcoFXPortable.exe"])
        self.initSetupEntry(self.DISCORD, ["C:/Users/Machin/AppData/Local/Discord/Update.exe",
                                           "--processStart",
                                           "Discord.exe"])

        self.initSetupEntry(self.STEAM, ["C:/Program Files (x86)/Steam/Steam.exe"])
        self.initSetupEntry(self.GOG, ["C:/Program Files (x86)/GOG Galaxy/GalaxyClient.exe"])
        self.initSetupEntry(self.EPIC,
                            ["C:/Program Files (x86)/Epic Games/Launcher/Portal/Binaries/Win32/EpicGamesLauncher.exe"])
        self.initSetupEntry(self.ITCHIO, ["G:/itchio/itch-setup.exe", "--prefer-launch" "--appname" "itch"])
        self.initSetupEntry(self.UBISOFT, ["C:/Program Files (x86)/Ubisoft/Ubisoft Game Launcher/Uplay.exe"])
        self.initSetupEntry(self.ORIGIN, ["C:/Program Files (x86)/Origin/Origin.exe"])
        self.initSetupEntry(self.GAME_TYPES, ["FPS", "RPG", "COOP", "VN", "SIMULATION"])
        self.initSetupEntry(self.GAME_STATUSES, ["TO BE STARTED", "IN PROGRESS", "ALTERNATIVE PLAY",
                                                 "IN STANDBY", "DONE"])
        self.initSetupEntry(self.GAME_NOTES, ["1", "2", "3", "4", "GIVUP"])
        self.initSetupEntry(self.EXTENDED_FILTER, [])
        self.initSetupEntry(self.INSTALLED_MODE, False)
        self.initSetupEntry(self.EXTENDED_MODE, False)

        #        self.initSetupEntry(self., )
        if print_mode:
            print("========================================================")

        if self.dirty:
            self.save()

    def initSetupEntry(self, name, default_value):
        reset = ""
        try:
            value = self.SBSGL[name]
        except KeyError:
            self.SBSGL[name] = default_value
            value = default_value
            self.dirty = True
        if self.print_mode:
            print(">>>>>>> {}: {}{}".format(name, value, reset))

    # set property value and generate KeyError is this is not a supported key entry
    # return previous value
    def set(self, name, value):
        old = self.SBSGL[name]
        self.SBSGL[name] = value
        if not self.dirty:
            print("Setup has been modified and has to be saved")
            self.dirty = True
        return old

    # get property value and generate KeyError is this is not a supported key entry
    def get(self, name):
        return self.SBSGL[name]

    def save(self):
        self.SETUP.save()
        self.dirty = False
