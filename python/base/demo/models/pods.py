from .base import Model, ModelList, LazyResponse

class Pod(Model):
    def __init__(self, name: str, ip_address: str, phase: str, state: str, claim: str):
        self.pod_name = name
        self.ip_address = ip_address
        self.phase = phase
        self.state = state
        self.claim = claim

class PodList(ModelList):
    def __init__(self, *items: Pod):
        super().__init__(*items)

class PodListResponse(LazyResponse):
    def __init__(self, pods: PodList):
        self.pods = pods
