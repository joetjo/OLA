from sbsgl.core.procmgr import ProcMgr


class SBSGL:
    def __init__(self):
        self.procmgr = ProcMgr()

    def stop(self):
        self.procmgr.stop()
