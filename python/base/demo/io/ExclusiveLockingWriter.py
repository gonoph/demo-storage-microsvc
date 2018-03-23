from threading import RLock
from fcntl import LOCK_EX

from . import SharedLockingWriter

class ExclusiveLockingWriter(SharedLockingWriter):
    def _additions(self):
        super(ExclusiveLockingWriter, self)._additions()
        self.tlock = RLock()

    def thread_ctrl(self, lock = True):
        if lock:
            self.tlock.acquire()
            self.logger.debug("Grabbing Thread Lock")
        else:
            self.tlock.release()
            self.logger.debug("Releasing Thread Lock")

    def truncate(self):
        with self.ctx:
            self.bof()
            self.file.truncate()

    @property
    def lock_op(self):
        return LOCK_EX
