from logging import getLogger
from random import randint
from time import sleep
from os import SEEK_SET, SEEK_END

from .ctx import CtxLock, CtxWriter, Writer
from ..settings import State

class LockingWriter(Writer):
    def __init__(self, path, pos = 0, whence = SEEK_SET, timeout = 5, demo_level = 0):
        self.logger = getLogger('.'.join((__name__, self.__class__.__name__)))
        self.file = open(path, 'a+')
        self.ctx = CtxWriter(self)
        self.timeout = timeout
        self.state = State()
        self.state.lock_count = 0
        self.state.lock_count_ctx = CtxLock()
        self.state.pos = 0
        self.demo_level = demo_level
        if demo_level > 0:
            if demo_level > 10:
                self.demo_level = 10
            self.logger.info("DEMO_LEVEL set to %d", demo_level)
        self._additions()

        self.eof()
        end = self.tell()
        if end < pos:
            self.bof()
            self.logger.warn("file was truncated: %s", path)
        else:
            self.seek(pos, whence)

    def _additions(self):
        """Child initializations"""

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file.close()

    def inc_lock_count(self):
        with self.state.lock_count_ctx:
            self.state.lock_count += 1
            return self.state.lock_count

    def dec_lock_count(self):
        with self.state.lock_count_ctx:
            if self.state.lock_count < 0:
                self.state.lock_count = 0
            else:
                self.state.lock_count -= 1
            return self.state.lock_count

    def seek(self, pos, whence = SEEK_SET):
        with self.ctx:
            self.file.seek(pos, whence)
            self.state.pos = self.file.tell()

    def eof(self):
        with self.ctx:
            self.file.seek(0, SEEK_END)
            if self.demo_level > 0:
                sleep(randint(1, self.demo_level * 2) / 1000)
            self.state.pos = self.file.tell()

    def bof(self):
        with self.ctx:
            self.file.seek(0)
            self.state.pos = self.file.tell()

    def flush(self):
        with self.ctx:
            self.file.flush()
            self.state.pos = self.file.tell()

    def tell(self):
        with self.ctx:
            return self.state.pos

    def iseof(self):
        with ctx:
            cur = self.file.tell()
            self.file.seek(0, SEEK_END)
            end = self.file.tell()
            self.state.pos = self.file.seek(cur)
            return end == self.state.pos

    def close(self):
        with self.ctx:
            return self.file.close()

    def write(self, line):
        with self.ctx:
            self.eof()
            start = self.tell()
            self.file.write(line)
            self.file.write('\n')
            self.state.pos = self.file.tell()
            return self.state.pos - start

    def read(self):
        lines = []
        with self.ctx:
            for line in self.file.readlines():
                lines.append(line.strip())
            self.state.pos = self.file.tell()
            return lines

    def _performLock(self):
        return True

    def _performUnlock(self):
        return True

    def lock(self):
        with self.state.lock_count_ctx:
            self.inc_lock_count()
            return self._performLock()

    def unlock(self):
        with self.state.lock_count_ctx:
            count = self.dec_lock_count()
            if count == 0:
                return self._performUnlock()
            return False
