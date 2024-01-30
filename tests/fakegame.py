import os
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import Label, Tk


class GhLauncher:

    @staticmethod
    def launch(label, exe):
        print("Launching {} ({}) from folder {} ".format(label, exe, os.getcwd()))
        bg = threading.Thread(target=GhLauncher.launchImpl, args=(exe,))
        bg.start()

    @staticmethod
    def launchImpl(exe):
        print("RUN-TH-{}".format(exe))
        subprocess.run(exe)


class Fake:

    def __init__(self, title):
        self.window = Tk()
        self.window.title("FAKEGAME V2 ({})".format(os.getpid()))
        Label(self.window, text=title).pack()

    def param(self, param):
        Label(self.window, text=param).pack()

    def start(self):
        self.window.mainloop()


APP = None

if __name__ == '__main__':
    print(f"Arguments count: {len(sys.argv)}")
    for i, arg in enumerate(sys.argv):
        if APP is None:
            APP = Fake(arg)
            APP.param("Current Folder: {}".format(os.getcwd()))
        elif Path(arg).is_file():
            APP.param("Launching {}".format(arg))
            GhLauncher.launch("start game", [arg])
        else:
            APP.param(arg)
        print(f"Argument {i:>6}: {arg}")

    APP.start()
