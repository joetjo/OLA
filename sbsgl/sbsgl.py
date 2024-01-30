import time
import threading

from sbsgl.JopLauncherConstant import JopSETUP
from sbsgl.core.procmgr import ProcMgr
from sbsgl.log import Log


def background(procmgr):
    """
    TODO: replace by QT Thread
    TODO: replace Log
    """
    sleep_time = 2
    delay = JopSETUP.get(JopSETUP.REFRESH_DELAY) / sleep_time
    Log.info("Core-Thread: Starting auto refresh thread - sleeping delay: {}s".format(delay * sleep_time))
    count = delay
    while not procmgr.shutdown:
        time.sleep(sleep_time)
        if procmgr.shutdown:
            Log.debug("Core-thread: stopping background thread")
            break
        elif count > delay:
            procmgr.refresh()
            count = 0
        else:
            count += 1


class SBSGL:
    def __init__(self):
        self.procmgr = ProcMgr()
        self.bg = threading.Thread(target=background, args=(self.procmgr,))

    def stop(self):
        self.procmgr.stop()
