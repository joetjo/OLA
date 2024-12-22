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
import logging
import pathlib

# Map Json storage for a session
from base.jsonstore import GhStorage
from sbsgl.core.private.process import ProcessInfo


class Session:

    def __init__(self, json, game_info=None):
        self.json = json
        self.json[2] = ProcessInfo.removeGameExtension(self.json[2])
        self.game_info = game_info
        self.installed = pathlib.Path(self.getPath()).is_file()

    def getName(self):
        return self.json[0]

    def setName(self, name):
        self.json[0] = name

    def getPath(self):
        return self.json[1]

    def setPath(self, value):
        self.json[1] = value

    def getOriginName(self):
        return self.json[2]

    def getLauncher(self):
        return self.json[3]

    def setLauncher(self, value):
        self.json[3] = value

    def getPlatform(self):
        return self.json[4]

    def setPlatform(self, value):
        self.json[4] = value

    def getCustomCommand(self):
        return self.json[5]

    def setCustomCommand(self, value):
        self.json[5] = value

    def getParameters(self):
        return self.json[6]

    def setParameters(self, value):
        self.json[6] = value

    def getSheet(self):
        return GhStorage.getValueOrEmptyString(self.game_info, 'sheet')

    def setSheet(self, value):
        self.game_info['sheet'] = value

    def getWWW(self):
        return GhStorage.getValueOrEmptyString(self.game_info, 'www')

    def setWWW(self, value):
        self.game_info['www'] = value

    def getTips(self):
        return GhStorage.getValueOrEmptyString(self.game_info, 'tips')

    def setTips(self, value):
        self.game_info['tips'] = value

    def getNote(self):
        return GhStorage.getValueOrEmptyString(self.game_info, 'note')

    def setNote(self, value):
        self.game_info['note'] = value

    def getStatus(self):
        return GhStorage.getValueOrEmptyString(self.game_info, 'status')

    def setStatus(self, value):
        self.game_info['status'] = value

    def getType(self):
        return GhStorage.getValueOrEmptyString(self.game_info, 'type')

    def setType(self, value):
        self.game_info['type'] = value

    # Only on search result ( not available for session from storage )
    def getGameInfo(self):
        return self.game_info


# encapsulate previous sessions management - List of Session managed
# either in storage ( last sessions )
# either in memory ( search result )
class SessionList:

    # Storage none --> im memory session list ( for search result )
    def __init__(self, storage=None, proc_manager=None):
        self.sessions = []
        self.json_sessions = []
        if storage is not None:
            self.json_sessions = storage.getOrCreate("last_sessions", [])
            for json in self.json_sessions:
                self.sessions.append(Session(json, proc_manager.find(json[0], "init session list")))
        # set storage after reading session
        self.storage = storage

    def list(self):
        return self.sessions

    # session : Session - in storage mode, remove existing session for same game before adding
    def addSession(self, session):
        if self.storage is None:
            self.sessions.append(session)
        else:
            if self.findSessionByName(session.getName()):
                self.removeSessionByName(session.getName())
            sheetName = session.getSheet()
            if sheetName is not None and len(sheetName) > 0:
                otherSession = self.findSessionBySheet(sheetName)
                while otherSession is not None:
                    logging.info("Merging multiple session for game sheet {} \n from previous session {} \n into latest running session {}".format(sheetName, otherSession.getPath(), session.getPath() ) )
                    session.game_info["duration"] = float(session.game_info["duration"]) + float(otherSession.game_info["duration"])
                    self.removeSessionByName(otherSession.getName())
                    otherSession = self.findSessionBySheet(sheetName)
            self.sessions.insert(0, session)
            self.json_sessions.insert(0, session.json)

    def findSessionByName(self, name):
        for session in self.sessions:
            if session.getName() == name:
                return session
        return None

    def findSessionBySheet(self, name):
        for session in self.sessions:
            if session.getSheet() == name:
                return session
        return None

    def renameSession(self, name, new_name):
        self.findSessionByName(name).name = new_name
        self.findJsonSessionEntryByName(name)[0] = new_name

    def findJsonSessionEntryByName(self, name):
        found = None
        for session in self.json_sessions:
            if session[0] == name:
                found = session
        return found

    # Returns the removed sessions
    def removeSessionByName(self, name):
        found = self.findSessionByName(name)
        if found is not None:
            self.sessions.remove(found)
            self.json_sessions.remove(self.findJsonSessionEntryByName(name))
        return found
