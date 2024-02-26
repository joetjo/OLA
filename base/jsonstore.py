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

import json
import logging


class GhStorage:

    # init from json file
    def __init__(self, json_file, content=None, version=0):
        if content is None:
            self.json_file = json_file
            self.content = {}
            self.version = version
            try:
                self.open()
            except FileNotFoundError:
                try:
                    self.create()
                except Exception as e:
                    logging.error("GhStorage:Failed to initialize storage on file {} : {}".format(self.json_file, e))
        else:
            # init from direct json content
            self.json_file = None
            self.content = content
            self.version = 0
            logging.info("GhStorage: transient usage")

    def open(self):
        if self.json_file is not None:
            with open(self.json_file, encoding='utf-8') as file:
                self.content = json.load(file)
                self.version = self.getOrCreate("version", 0)
            logging.info("GhStorage: loaded - version {}".format(self.version))
        else:
            logging.info("GhStorage: open ignored, not open from file")

    def create(self):
        if self.json_file is not None:
            logging.info("GhStorage: Creating local storage {}".format(self.json_file))
            with open(self.json_file, "w", encoding='utf-8') as file:
                file.write("{\"version\" : {} }".format(self.version))
            self.open()
        else:
            logging.info("GhStorage: create ignored, not open from file")

    def reset(self, content):
        self.content = content
        if self.json_file is not None:
            self.save()

    def save(self):
        if self.json_file is not None:
            with open(self.json_file, "w", encoding='utf-8') as file:
                json.dump(self.content, file, ensure_ascii=False, indent=4)
                logging.info("GhStorage: {} saved".format(self.json_file))
        else:
            logging.info("GhStorage: save ignored, not open from file")

    def getVersion(self):
        return self.version

    def setVersion(self, version):
        self.version = version
        self.content["version"] = version

    def data(self):
        return self.content

    def getOrCreate(self, key, default):
        try:
            return self.content[key]
        except KeyError:
            self.content[key] = default
            self.save()
            return self.content[key]

    @staticmethod
    def getValue(data, key):
        try:
            return data[key]
        except:
            return None

    @staticmethod
    def getValueOrEmptyString(data, key):
        try:
            return data[key]
        except:
            return ""
