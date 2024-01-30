# Copyright 2024 joetjo https://github.com/joetjo/MarkdownHelper
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

from pathlib import Path

from base.jsonstore import GhStorage


class GhSetup(GhStorage):

    def __init__(self, appname, content=None, path=None):
        if content is None:
            if path is None:
                home = str(Path.home())
            else:
                home = path
            self.filename = "{}/.{}.json".format(home, appname)
            super(GhSetup, self).__init__(self.filename)

            try:
                self.setup = self.data()['global']
            except KeyError:
                self.data()['global'] = {}
                self.save()
                self.setup = self.data()['global']

            print("GhSetup: Configuration loaded")
        else:
            super(GhSetup, self).__init__(appname, content)

    # get string value with name key
    def setup(self, key):
        try:
            return self.setup[key]
        except KeyError:
            self.setup[key] = ""
            return self.setup[key]

    # get bloc value with name key
    def getBloc(self, key):
        try:
            return self.content[key]
        except KeyError:
            self.content[key] = {}
            return self.content[key]
