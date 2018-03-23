from .base import Model, LazyResponse
from .pods import Pod

class Remote(Model):
    def __init__(self, pod: Pod, url: str, rc: int, message: str, headers: dict, body: str, fault: str):
        self.pod = pod
        self.url = url
        self.rc = rc
        self.message = message
        self.headers = dict(**headers)
        self.body = body
        self.fault = fault

class RemoteResponse(LazyResponse):
    def __init__(self, remote: Remote):
        self.remote = remote
