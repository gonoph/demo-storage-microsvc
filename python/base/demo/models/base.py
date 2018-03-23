from typing import List, Tuple, Dict, TypeVar, Generic, Sequence
from logging import getLogger

logger = getLogger(__name__)

class Model(object):
    def _to_primative(item):
        if item is None:
            return None
        logger.debug("to_primative(%s)", item)
        if isinstance(item, dict):
            return dict(Model._to_primative(list(item.items())))
        if isinstance(item, tuple):
            item = list(item)
        if isinstance(item, set):
            item = list(item)
        if isinstance(item, list):
            l = list()
            for i in item:
                l.append(Model._to_primative(i))
            return l
        if isinstance(item, Model):
            return Model._to_primative(item.__dict__)
        return item

    def __repr__(self):
        ret = "%s(" % self.__class__.__name__
        vals = set()
        for (k,v) in self.__dict__.items():
            vals.add("%s=%s" % (k, v))
        ret += '; '.join(vals)
        ret += ')'
        return ret

    def asdict(self):
        return Model._to_primative(self)

class ModelList(Model):
    def __init__(self, *items):
        if items:
            self.num = len(items)
            self.items = items
            assert not isinstance(items[0], list)
            assert not isinstance(items[0], tuple)
        else:
            self.num = 0
            self.items = []

class Response(Model):
    def __init__(self, hostname: str, rc: int, message: str, fault: str, timer:float):
        self.hostname = hostname
        self.rc = rc
        self.message = message
        self.fault = fault
        self.timer = timer * 1.0

class LazyResponse(Model):
    def add_response(self, response: Response):
        d = dict(**response.__dict__)
        d.update(self.__dict__)
        self.__dict__ = d
