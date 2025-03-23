import json


class GhPersistentList:

    def __init__(self, path):
        self.path = path
        try:
            with open(path, 'r') as openfile:
                self.values = json.load(openfile)
        except FileNotFoundError:
            self.values = dict()
            self.save()

    def save(self):
        with open(self.path, "w") as outfile:
            json.dump(self.values, outfile)

    def get(self, name):
        try:
            return self.values[name]
        except KeyError:
            return ""

    def set(self, name, value):
        self.values[name] = value