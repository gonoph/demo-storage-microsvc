from threading import RLock

class Writer(object):
    def lock(self):
        raise NotImplementedError();

    def unlock(self):
        raise NotImplementedError();

class CtxWriter(object):
    def __init__(self, writer: Writer):
        self.writer = writer
    def __enter__(self):
        self.writer.lock()
        return self
    def __exit__(self, type, value, traceback):
        self.writer.unlock()

class CtxLock(object):
    def __init__(self):
        self.tlock = RLock()
    def __enter__(self):
        self.tlock.acquire()
        return self
    def __exit__(self, type, value, traceback):
        self.tlock.release()
