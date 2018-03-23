from flask import g
from logging import getLogger
from werkzeug.exceptions import default_exceptions
from time import time

from .decorators import make_fault_response

logger = getLogger(__name__)

def timer_pre_handler():
    """handler to track the time of requests"""
    g.begin = time()

def error_handler(e):
    """handler to ensure uncaught errors are expressed as json"""
    description = getattr(e, 'description', str(e))
    code = getattr(e, 'code', 500)
    name = getattr(e, 'name', e.__class__)
    return make_fault_response(description, rc=code, message="%d %s" % (code, name))

# initialize the error_handler to handle all errors
def _init_handlers(app):
    """register the error_handler for all errors"""
    logger.info("Registering handlers to flask")
    app.before_request(timer_pre_handler)
    logger.debug("Registered timer_pre_handler as before_request")
    for e in default_exceptions:
        app.register_error_handler(e, error_handler)
        logger.debug("Registered error_handler for exception: %s", e)
