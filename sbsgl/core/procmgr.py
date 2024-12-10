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

# psutil must not be imported --> all call inside ProcessUtil for easy test purpose
import copy
import logging  # This module is thread safe.
import threading
import time

from sbsgl.SbSGLLauncherConstant import SbSGLLauncher, SbSGLSETUP
from base.jsonstore import GhStorage
from sbsgl.data.session import SessionList, Session
from sbsgl.core.migrations.migrate import StorageVersion
from sbsgl.core.private.currentgame import GameProcessHolder
from sbsgl.core.private.process import ProcessInfo
from sbsgl.core.private.processutil import ProcessUtil
from sbsgl.sbsglsetup import SbSGLSetup

LOCAL_STORAGE = 'local_storage.json'
LOCK = threading.Lock()

GAME_TEMPLATE = {
    "duration": "0",
    "last_duration": "0",
    "last_session": "0",
    "note": "",
    "www": "",
    "tips": "",
    "sheet": "",
    "type": "",
    "status": ""
}


class ProcMgr:

    def __init__(self):
        self.process_util = ProcessUtil()
        self.shutdown = False
        self.plist = dict()
        self.currentGame = GameProcessHolder()
        self.previousGame = GameProcessHolder()

        self.storage = GhStorage(LOCAL_STORAGE, "SBSGL", version=SbSGLLauncher.DB_VERSION)
        StorageVersion.check_migration(self.storage, SbSGLLauncher.DB_VERSION)

        try:
            self.games = self.storage.data()["Games"]
        except KeyError:
            self.storage.reset({"Games": {}})
            self.games = self.storage.data()["Games"]

        self.sessions = SessionList(self.storage, self)
        self.game_mappings = self.storage.getOrCreate("mappings", {})
        self.game_ignored = self.storage.getOrCreate("ignored", [])
        self.game_launchers = self.storage.getOrCreate("launchers", {})

        # Running platforms
        self.platforms = []
        self.others = []
        self.games_platforms = [""]
        for key in SbSGLLauncher.GAME_PLATFORMS:
            self.games_platforms.append(SbSGLLauncher.GAME_PLATFORMS[key])

        # Game properties
        self.games_types = SbSGLSETUP.get(SbSGLSetup.GAME_TYPES)
        self.games_statuses = SbSGLSETUP.get(SbSGLSetup.GAME_STATUSES)
        self.games_notes = SbSGLSETUP.get(SbSGLSetup.GAME_NOTES)

    # Returns current game if current game is still running
    def getCurrentGameDetected(self):
        try:
            if self.currentGame.isSet() and self.plist[self.currentGame.pid] is not None:
                return self.currentGame
            else:
                return None
        except KeyError:
            return None

    def resetCurrentGame(self, name):
        if LOCK.acquire(True):  # blocking
            detected_game = self.getCurrentGameDetected()
            if detected_game is not None and detected_game.getName() == name:
                self.previousGame = GameProcessHolder(self.currentGame)
                self.currentGame.reset()
            LOCK.release()

    def loadPList(self):
        self.plist = dict()
        platforms = []
        others = []

        #
        # Retrieve Process List
        #
        for process_name in self.process_util.process_iter():
            # Fetch process details as dict
            p = ProcessInfo(self.process_util.readProcessAttributes(process_name))
            if p is not None:
                self.plist[p.getPid()] = p

        #
        # Check if last detected game is still running -> if YES then no game discovery
        #    But check is game is not been ignored or define as a launcher
        #
        game_detected = self.getCurrentGameDetected()
        if game_detected is None and self.currentGame.isSet():
            self.previousGame = GameProcessHolder(self.currentGame)
            logging.debug("CORE: Game end detected: {}".format(self.previousGame.getName()))
            self.currentGame.reset()

        if game_detected is not None:
            logging.debug("CORE: Last detected game still running ({})".format(game_detected.getName()))
            if self.isLauncher(game_detected.getName()) or self.isIgnore(game_detected.getName()):
                logging.debug("CORE:   --> current running game has been excluded or is a launcher")
                # Let's forget about it !
                self.currentGame.reset()

        #
        # Game discovery ( if no current game )
        #
        if not self.currentGame.isSet():
            for pid, p in self.plist.items():
                if p.isGame():  # Yeeesss that's what we search
                    p.removeExtension()  # Remove the extension before any action

                    mapping = self.getMapping(p.getName())  # check if a mapping is defined
                    if mapping is not None:
                        p.forceName(mapping)

                    if not self.isLauncher(p.getName()) and \
                            not self.isIgnore(p.getName()):  # Ignore launcher and excluded game

                        # This is a really game !!
                        logging.debug("PList -game detected {}".format(p.getName()))
                        if not self.currentGame.isSet():
                            #
                            # new game detected
                            #
                            self.currentGame.setProcess(p)
                            store_entry = self.find(p.getName(), "loading plist: process discovery")
                            if store_entry is None:
                                # TODO mapping name may be identical to a real other process name - to check
                                logging.info("New game discovered : creating game {} within storage".format(p.getName()))
                                self.games[p.getName()] = copy.deepcopy(GAME_TEMPLATE)
                                p.setStoreEntry(self.games[p.getName()])
                                self.storage.save()
                            else:
                                p.setStoreEntry(store_entry)
                                lastSession = self.sessions.findSessionByName(p.getName())
                                if lastSession is not None and not lastSession.getPath() == p.getPath():
                                    logging.info("Game {} : path has changed since last play ! Updating from {} to {}"
                                             .format(p.getName(), lastSession.getPath(), p.getPath()))
                                    lastSession.setPath(p.getPath())
                                    self.storage.save()

                            p.setStarted()
                            self.currentGame.setProcess(p)

                            session = self.sessions.findSessionByName(self.currentGame.getName())
                            if session is None:
                                session = Session(
                                    [self.currentGame.getName(), p.path, p.getOriginName(), "", "", "", ""],
                                    self.find(self.currentGame.getName(),
                                              "loading plist: processing 1st game session declaration"))
                                self.sessions.addSession(session)
                            else:
                                # Path update in case game has been moved or updated
                                session.setPath(p.path)
                        else:
                            logging.info("More than one game detected ! {} is ignored".format(self.currentGame.getName()))
                    else:
                        logging.debug("Process {} exclude".format(self.currentGame.getName()))
                elif p.game_platform is not None:
                    if p.game_platform not in platforms:
                        platforms.append(p.game_platform)
                elif p.other is not None:
                    if p.other not in others:
                        others.append(p.other)
        else:
            for pid, p in self.plist.items():
                if p.game_platform is not None and p.game_platform not in platforms:
                    platforms.append(p.game_platform)
                if p.other is not None and p.other not in others:
                    others.append(p.other)

        logging.debug("CORE: {} processes detected / {} game(s) platforms / {} Other(s) / {}".format(len(self.plist),
                                                                                                 len(platforms),
                                                                                                 len(others),
                                                                                                 self.currentGame.getName()))
        #
        # Check for running game platform
        #
        self.others = others
        self.platforms = platforms

        #
        # Check if current game has been stopped
        #
        if self.previousGame is not None \
                and self.previousGame.isSet():

            new_duration = self.previousGame.process.setStopped()

            store = self.previousGame.process.getStoreEntry()
            try:
                duration = float(store["duration"])
            except KeyError:
                duration = 0.0
            store["duration"] = str(duration + new_duration.total_seconds())
            store["last_duration"] = str(new_duration.total_seconds())
            store["last_session"] = str(time.time())
            self.sessions.addSession(self.sessions.findSessionByName(self.previousGame.getName()))

            self.storage.save()

            self.previousGame = None

    @staticmethod
    def toString(pdict):
        message = ""
        for key in pdict:
            message = "{} {} {} |".format(message, key, pdict[key].getName())
        return message

    def refresh(self):
        if LOCK.acquire(False):  # Non-blocking -- return whether we got it
            logging.debug('CORE: Refreshing...')
            self.loadPList()
            LOCK.release()
        else:
            logging.info("CORE: Couldn't get the lock. Maybe next time")

    def getSessions(self):
        """
        :return: List of Session
        """
        return self.sessions.list()

    def get(self, pid):
        return self.plist.get(pid)

    # Returns the entry with the exact name provided ( unique )
    def find(self, name, context):
        try:
            return self.games[name]
        except KeyError:
            logging.debug("{} - Warning : Game {} not found (ok if 1st run only)".format(context, name))
            return None

    def findSessionBySheetName(self, sheetName):
        return self.sessions.findSessionBySheet(sheetName)

    # Returns all games with the token in their name within the storage
    def searchInStorage(self, token):
        result = SessionList()
        for game_name in self.games:
            if token in game_name:
                last = self.sessions.findSessionByName(game_name)
                if last is None:
                    # not played in last sessions ( no session data - empty one should be used to display the result
                    last = Session([game_name, "", game_name, "", "", "", ""], self.games[game_name])
                result.addSession(last)
        return result

    def getCurrentGame(self):
        """
        :return: GameProcessHolder
        """
        if self.currentGame.isSet():
            return self.currentGame
        else:
            return None

    def isIgnore(self, name):
        return name in self.game_ignored

    def remove(self, name):
        session = self.sessions.removeSessionByName(name)
        if name in self.games:
            del self.games[name]
        if session is not None and session.getOriginName() in self.game_mappings:
            mapping = self.game_mappings[session.getOriginName()]
            if mapping != 'PARENT':
                del self.game_mappings[name]
        self.storage.save()

    def removeExcluded(self, name):
        if self.isIgnore(name):
            self.game_ignored.remove(name)
            self.storage.save()

    def ignore(self, name):
        if not self.isIgnore(name):
            self.remove(name)
            self.game_ignored.append(name)
            self.resetCurrentGame(name)
            self.storage.save()

    def isLauncher(self, name):
        return GhStorage.getValue(self.game_launchers, name) is not None

    def removeLauncher(self, name):
        if self.isLauncher(name):
            del self.game_launchers[name]
            self.storage.save()

    def addLauncher(self, name, path):
        if not self.isIgnore(name):
            self.game_launchers[name] = path
            self.resetCurrentGame(name)
            self.storage.save()

    def getMapping(self, name):
        return GhStorage.getValue(self.game_mappings, name)

    # set or overwrite mapping
    def addMapping(self, session, map_name):
        current_name = session.getName()
        new_name = ProcessInfo.getMapName(session.getPath(), map_name)

        # mapping are always stored using the original name
        self.game_mappings[session.getOriginName()] = map_name

        # update existing session stored with the current name
        self.sessions.renameSession(current_name, new_name)

        # update name in game list
        if current_name in self.games:
            self.games[new_name] = self.games[current_name]
            del self.games[current_name]

        self.storage.save()

    def getLauncher(self, name):
        return GhStorage.getValue(self.game_launchers, name)

    def getLaunchers(self):
        result = [""]
        for key in self.game_launchers:
            result.append(key)
        return result

    def getRunningPlatforms(self):
        return self.platforms

    def getPossiblePlatforms(self):
        return self.games_platforms

    def getPossibleTypes(self):
        return self.games_types

    def getPossibleStatuses(self):
        return self.games_statuses

    def getPossibleNotes(self):
        return self.games_notes

    def stop(self):
        self.shutdown = True
