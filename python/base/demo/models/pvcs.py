from .base import Model, ModelList, LazyResponse

class Pvc(Model):
    def __init__(self, name: str, mode: str, capacity: str):
        self.name = name
        self.mode = mode
        self.capacity = capacity

class PvcList(ModelList):
    def __init__(self, *items: Pvc):
        super().__init__(*items)

class PvcListResponse(LazyResponse):
    def __init__(self, pvcs: PvcList):
        self.pvcs = pvcs
