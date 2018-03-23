from functools import wraps, lru_cache
from threading import RLock, Lock, local, Condition, Thread
from time import time
from demo import State
import logging

logger = logging.getLogger("demo.%s" % __name__)
logger.setLevel(logging.NOTSET)

def expiring_cache(timeout=5, maxsize=32):
    """decorator to cache a function via lru_cache, but expire the cache
    after a timeout"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time()
            last = state.last
            timer = now - last
            if timer > timeout:
                logger.info("timeout (%d) reached, clearing cache", timeout)
                cached.cache_clear()
                state.last = now
            logger.debug("timer=%d; timeout=%d; cache=%s",
                timer, timeout, cached.cache_info())
            return cached(*args, **kwargs)

        @lru_cache(maxsize=maxsize)
        def cached(*args, **kwargs):
            return func(*args, **kwargs)

        state = State()
        state.last = 0
        return wrapper
    return decorator

ThreadCount=1
def Async():
    """decorator to run a callable in it's own thread. Dangerous as it doesn't
    use pools If there are any errors, the return type of the function is
    changed to a Future object that wraps the return value (ret) and any
    exceptions (ex). It also provides a join() method. """
    def decorator(func):
        class Future(object):
            ThreadCount = 1
            def __init__(self, func, args, kwargs):
                self.func = func
                self.ex = None
                self.ret = None
                self.alive = True
                self.args = args
                self.kwargs = kwargs
                self.thread = Thread(
                    name="Thread-%s-%d" % (func.__name__, Future.ThreadCount),
                    target=self.doit)
                self.thread.start()
                Future.ThreadCount+=1
            def doit(self):
                args = self.args
                kwargs = self.kwargs
                try:
                    self.ret = self.func(*args, **kwargs)
                    return self.ret
                except Exception as ex:
                    self.ex = ex
                    raise ex
                finally:
                    self.alive = False

            def join(self, ignoreErrors = False):
                self.thread.join()
                if self.ex is not None and not self.ignoreErrors:
                    raise self.ex
                return self.ret
        @wraps(func)
        def wrapper(*args, **kwargs):
            return Future(func, args, kwargs)
        return wrapper
    return decorator

def IgnoreErrors(empty=None):
    """Decorator to ignore, but catch errors on a callable. See any exceptions
    via the added ex() method. Exceptions are stored by thread."""
    def decorator(func):
        ll = local()
        @wraps(func)
        def wrapper(*args, **kwds):
            ll.ex = None
            try:
                logger.debug("About to enter function[%s]", func.__name__)
                return func(*args, **kwds)
            except Exception as ex:
                ll.ex = ex
                logger.warn("Caught error; ignoring it: %s", ex if ex.args else repr(ex))
            return empty
        def ex():
            return ll.ex
        wrapper.ex = ex
        return wrapper
    return decorator

class TimeoutException(Exception):
    """An Exception when a Timeout has been reached."""

def Synchronized(lock = None, condition_lock = None, timeout = 15):
    """Decorator to synchonize a callable by threads using an RLock, or other
    class with acquire and release methods."""
    if lock is None:
        lock = RLock()
    if condition_lock is None:
        condition_lock = RLock()
    def decorator(func):
        name = func.__name__
        condition = Condition(condition_lock)
        @wraps(func)
        def wrapper(*args, **kwds):
            logger.debug("func[%s] lock is %s", name, lock)
            logger.debug("func[%s] Getting lock for wrapper", name)
            condition.acquire()
            try:
                if not lock.acquire(False):
                    logger.debug("func[%s] waiting [%d] secs for lock to free", name, timeout)
                    condition.wait(timeout=timeout)
                    if not lock.acquire(False):
                        raise TimeoutException("func[%s] Timed out waitng on lock %s" % (name, lock))
            finally:
                condition.release()
            try:
                return func(*args, **kwds)
            finally:
                condition.acquire()
                lock.release()
                condition.notify()
                condition.release()
                logger.debug("func[%s] Released wrapper lock", name)
        return wrapper
    return decorator
