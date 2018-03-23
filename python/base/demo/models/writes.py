from .base import Model, LazyResponse

class Writes(Model):
    def __init__(self, bytes_written: int, entries: int):
        self.bytes = bytes_written
        self.entries = entries

class WritesResponse(LazyResponse):
    def __init__(self, writes: Writes):
        self.writes = writes
