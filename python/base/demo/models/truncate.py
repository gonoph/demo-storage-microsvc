from .base import Model, LazyResponse

class TruncatedResponse(LazyResponse):
    def __init__(self, message: str, file: str, truncated: bool):
        self.message = message
        self.file = file
        self.truncated = truncated
