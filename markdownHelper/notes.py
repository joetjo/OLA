import json


class MhNotes:

    def __init__(self, path):
        self.path = path
        try:
            with open(path, 'r') as openfile:
                self.notes = json.load(openfile)
        except FileNotFoundError:
            self.notes = dict()
            self.save()

    def save(self):
        with open(self.path, "w") as outfile:
            json.dump(self.notes, outfile)

    def get(self, name):
        try:
            return self.notes[name]
        except KeyError:
            return ""

    def set(self, name, value):
        self.notes[name] = value