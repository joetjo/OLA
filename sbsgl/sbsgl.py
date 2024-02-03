import os

from sbsgl.core.procmgr import ProcMgr
from sbsgl.tools import SgSGLLauncher, OLABackend


class SBSGL:
    def __init__(self):
        self.procmgr = ProcMgr()

    def stop(self):
        self.procmgr.stop()

    def launchGame(self, session, app):
        launcher = session.getLauncher()
        custom = session.getCustomCommand()
        if launcher is not None and len(launcher) > 0:
            exe = [self.procmgr.getLauncher(launcher), session.getPath()]
        elif custom is not None and len(custom) > 0:
            exe = [custom]
        else:
            exe = [session.getPath()]
        params = session.getParameters().strip()
        if params is not None and len(params) > 0:
            for p in params.split(" "):
                exe.append(p)
        exeFolder = os.path.dirname(exe[0])
        launcher = SgSGLLauncher(session.getName(), exe, exeFolder)
        launcher.signals.ok.connect(app.gameLaunched)
        launcher.signals.ko.connect(app.gameLaunchFailure)
        OLABackend.THPOOL.start(launcher)
