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

from sbsgl.JopLauncherConstant import JopLauncher
from sbsgl.log import Log


def nop(storage, version):
    Log.debug("| no data migration needed to upgrade to version {}".format(version))


def toV2(storage, version):
    last_session = storage.data()['last_sessions']
    for s in last_session:
        s.append("")  # Launcher
        s.append("")  # platform
        s.append("")  # custom command
        s.append("")  # custom parameters


def toV3(storage, version):
    games = storage.data()['Games']

    for key, value in games.items():
        value["type"] = ""


def toV4(storage, version):
    games = storage.data()['Games']

    for key, value in games.items():
        value["status"] = ""
        try:
            value["sheet"] = value["note"]
        except KeyError:
            value["sheet"] = ""
        value["note"] = ""


class StorageVersion:
    VERSION_LIST = [0,
                    1,
                    2,
                    4,
                    JopLauncher.DB_VERSION]

    MIGRATIONS_STEP = [nop,
                       nop,
                       toV2,
                       toV3,
                       toV4]

    @staticmethod
    def check_migration(storage, to):
        if storage.getVersion() != to:
            current = storage.getVersion()
            Log.info("Storage migration from {} to {}".format(current, to))
            for idx in range(0, len(StorageVersion.VERSION_LIST)):
                v = StorageVersion.VERSION_LIST[idx]
                if current < v:
                    StorageVersion.MIGRATIONS_STEP[v](storage, v)
            storage.setVersion(to)
            storage.save()
