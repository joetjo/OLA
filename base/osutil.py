import subprocess, os, platform


class OSUtil:
    @staticmethod
    def systemOpen(action):
        if platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', action))
        elif platform.system() == 'Windows':  # Windows
            os.startfile(action)
        else:  # linux variants
            subprocess.call(('xdg-open', action))
