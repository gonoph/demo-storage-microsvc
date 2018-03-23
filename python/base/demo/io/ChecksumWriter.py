from time import time
from base64 import b64decode, b64encode
from threading import local, current_thread
from hashlib import sha256
from os import urandom, getpid

from .. import models, State
from .ctx import CtxLock
from .LockingWriter import LockingWriter

class ChecksumWriter(LockingWriter):
    tracker = local()
    def _additions(self):
        self.state.errors = []
        self.state.errors_ctx = CtxLock()
        self.state.failed = []
        self.state.failed_ctx = CtxLock()
        self.buffer = State()
        self.buffer.chk = None
        self.buffer.chk_header = ('', 0, 0)

    def inc_sequence(self):
        state = getattr(ChecksumWriter.tracker, 'state', None)
        if state is None:
            state = State()
            state.seq = 0
            ChecksumWriter.tracker.state = state
        state.seq += 1
        return state.seq

    def header(self):
        return "%15x:%05d:%06d" % (current_thread().ident, getpid(), self.inc_sequence())

    @property
    def errors(self):
        with self.state.errors_ctx:
            errors = list(self.state.errors)
            self.state.errors = []
            return models.ErrorRecordList(*errors)

    @errors.setter
    def errors(self, value):
        with self.state.errors_ctx:
            self.state.errors.append(value)

    @property
    def failed_checksum(self):
        with self.state.failed_ctx:
            failed = list(self.state.failed)
            self.state.failed = []
            return models.FailedRecordList(*failed)

    @failed_checksum.setter
    def failed_checksum(self, value):
        with self.state.failed_ctx:
            self.state.failed.append(value)

    def write(self, line: str):
        header = self.header()
        written = 0
        b = urandom(32) + line.encode('utf-8')
        with self.ctx:
            h = sha256(b).hexdigest()
            written += self._writeline(header, 'C', h)
            t = b64encode(b).decode('utf-8')
            written += self._writeline(header, 'D', t)
            return models.Writes(written, 1)

    def _writeline(self, *items):
        with self.ctx:
            self.eof()
            start = self.file.tell()
            self.file.write(':'.join(items))
            self.file.write('\n')
            self.state.pos = self.file.tell()
            return self.state.pos - start

    def read(self):
        state = State()
        state.lines = []
        state.partial = False
        state.initial = True
        state.time = time()
        with self.ctx:
            while state.initial or state.partial:
                state.initial = False
                if (time() - state.time) >= self.timeout:
                    raise IOError("Read timeout!")
                for line in self.file.readlines():
                    self.logger.debug("Line: %s", line.strip())
                    fields = line.split(':')
                    # this prevents it from throwing an unpack error
                    fields = list(map(lambda x: fields[x] if x < len(fields) else '', range(5)))
                    (name, pid, seq, ty, txt) = fields
                    if ty == 'C':
                        state.partial = True
                        self.buffer.chk = txt.strip()
                        self.buffer.chk_header = ':'.join((name, pid, seq))
                    else:
                        state.partial = False
                        dat_header = ':'.join((name, pid, seq))
                        dat = txt.strip()
                        b = b64decode(dat.encode('utf-8'))
                        data = b[32:].decode('utf-8')
                        if self.buffer.chk_header != dat_header:
                            record = models.ErrorRecord(
                                self.buffer.chk_header,
                                dat_header,
                                data)
                            self.logger.warn("Invalid Record: %s",
                                record)
                            self.errors = record
                            continue
                        h = sha256(b).hexdigest()
                        if self.buffer.chk == h:
                            record = models.GoodRecord(data)
                            self.logger.info("%s - %s: %s",
                                self.buffer.chk_header,
                                'GOOD',
                                data
                                )
                            state.lines.append(record)
                        else:
                            record = models.FailedRecord(
                                self.buffer.chk_header,
                                h,
                                data)
                            self.logger.warn("Failed Checksum: %s", record)
                            self.failed_checksum = record
                        self.buffer.chk = None
                        self.buffer.chk_header = ('', 0, 0)
                self.state.pos = self.file.tell()
            return models.GoodRecordList(*state.lines)
