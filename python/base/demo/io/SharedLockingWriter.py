from fcntl import flock, LOCK_SH, LOCK_UN

from . import ChecksumWriter

class SharedLockingWriter(ChecksumWriter):
    @property
    def lock_op(self):
        return LOCK_SH

    @property
    def unlock_op(self):
        return LOCK_UN

    def thread_ctrl(self, lock = True):
        pass

    def _performLock(self):
        self.thread_ctrl(True)
        flock(self.file, self.lock_op)
        return True

    def _performUnlock(self):
        flock(self.file, self.unlock_op)
        self.thread_ctrl(False)
        return True
