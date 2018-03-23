from socket import gethostname
from threading import local
from os import getenv
from logging import warn, getLogger, INFO, WARNING, NOTSET, getLevelName, root as logging_root, basicConfig
from logging.config import fileConfig

logger = getLogger(__name__)

class State(object):
    """track state"""
    def __init__(self):
        self.logger = getLogger('.'.join((__name__, self.__class__.__name__)))

class EnvState(State):
    def fromenv(self, name, default, converter = str):
        self.logger.debug("Reading [%s] from env with default(%s) and using converter(%s)",
            name, default, converter)
        val = default
        try:
            _val = getenv(name, default)
            val = converter(_val) if default is not None else _val
        except ValueError as ex:
            self.logger.warn("Ignoring error reading(%s) from environment: %s", name, ex)
        self.__dict__[name] = val
    def fromfile(self, key, path, default, converter = str):
        self.logger.debug("Reading [%s] from file(%s) with default(%s) and using converter(%s)",
            key, path, default, converter)
        val = default
        if path is not None:
            try:
                with open(path, 'r') as f:
                    _val = f.read().strip()
                    val = converter(_val)
            except Exception as ex:
                self.logger.warn("Ignoring error reading(%s) from file(%s): %s", key, path, ex)
        self.__dict__[key] = val

_logging_level = NOTSET

def _boostrap_logging():
    # this is useful for testing, and a real environment should be
    # createing a logging environment before this runs
    if not logging_root.handlers:
        warn("Setting up basic logging")
        _state = EnvState()
        _state.fromenv('LOGCONFIG', 'logging.conf')
        fileConfig(_state.LOGCONFIG)

        root_log_level = logging_root.level

        flask_logger = getLogger('werkzeug')
        if flask_logger.level == 0 and root_log_level > INFO:
            flask_logger.setLevel(INFO)

def _init_state():
    logger.info("Initializing state from environment variables")
    state.fromenv('KUBERNETES_CA_PATH', None)
    state.fromenv('KUBERNETES_TOKEN_PATH', None)
    state.fromenv('KUBERNETES_NAMESPACE_PATH', '/run/secrets/kubernetes.io/serviceaccount/namespace')
    state.fromenv('NAME', 'test')
    state.fromenv('DEMO_FILE_PATH', '/tmp/demo.db')
    state.fromenv('DEMO_READ_TIMEOUT', 5, int)
    state.fromenv('DEMO_HOST_OVERRIDE', None)
    state.fromenv('DEMO_PORT', '8080')
    state.fromenv('DEMO_REQUEST_TIMEOUT', 5, int)
    state.fromfile('namespace', state.KUBERNETES_NAMESPACE_PATH, 'test')
    state.fromfile('kubernetes_token', state.KUBERNETES_TOKEN_PATH, None)
    state.threaded = local()
    state.hostname = gethostname()

state = EnvState()
_boostrap_logging()
_init_state()
del _boostrap_logging
del _init_state
