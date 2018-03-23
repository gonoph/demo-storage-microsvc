from .base import Model, ModelList, LazyResponse

GoodRecord=str

class GoodRecordList(ModelList):
    def __init__(self, *items: GoodRecord):
        super().__init__(*items)

class ErrorRecord(Model):
    def __init__(self, check_header: str, data_header: str, data: str):
        self.check_header = check_header
        self.data_header = data_header
        self.data = data

class ErrorRecordList(ModelList):
    def __init__(self, *items: ErrorRecord):
        super().__init__(*items)

class FailedRecord(Model):
    def __init__(self, stored_hash: str, calculated_hash: str, data: str):
        self.stored_hash = stored_hash
        self.calculated_hash = calculated_hash
        self.data = data

class FailedRecordList(ModelList):
    def __init__(self, *items: FailedRecord):
        super().__init__(*items)

class ReadCollection(Model):
    def __init__(self, pos:int, records: GoodRecordList, errors: ErrorRecordList, fails: FailedRecordList):
        self.pos = pos
        self.records = records
        self.errors = errors
        self.fails = fails

class ReadResponse(LazyResponse):
    def __init__(self, reads: ReadCollection):
        self.reads = reads
