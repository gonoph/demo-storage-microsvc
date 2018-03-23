from logging import getLogger
from functools import wraps
from flask import make_response, g, jsonify, current_app, stream_with_context
from time import time, sleep

from .. import state
from .. import models

logger = getLogger(__name__)

def json_response(func):
    """decorator ensure responses are expressed as json"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            resp = func(*args, **kwargs)
            return make_ok_response(resp)
        except Exception as ex:
            logger.exception("Exception caught in %s(%s, %s)", func, args, kwargs)
            return make_fault_response(ex)
    return wrapper

def plain_response(mimetype='text/plain'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            resp = current_app.response_class(ret, mimetype=mimetype)
            return resp, 200, add_custom_headers()
        return wrapper
    return decorator

def stream_response(mimetype='text/event-stream', timeout=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time();
            def generate():
                _running = True
                _old = getattr(g, 'stream_tracker', None)
                while _running:
                    ret = func(*args, **kwargs)
                    _new = getattr(g, 'stream_tracker', ret)
                    if _new != _old:
                        _old = _new
                        # print(ret)
                        start = time()
                        yield 'event: message\ndata: ' + ret + '\n\n'
                    sleep(1)
                    g.begin = time()
                    if (g.begin - start) > timeout:
                        _msg = 'Waited to long for response, ending request'
                        logger.warn(_msg)
                        _running = False
                        # break
                        yield 'event: timeout\ndata: ' + _msg + '\n\n'
            return current_app.response_class(
                stream_with_context(generate()),
                status=200,
                headers=add_custom_headers(),
                mimetype=mimetype)
        return wrapper
    return decorator

def make_ok_response(item, pretty_json=True):
    response = models.Response(state.hostname, 200, 'Ok', None, (time() - g.begin) * 1000)
    if isinstance(item, models.LazyResponse):
        item.add_response(response)
    if isinstance(item, models.Model):
        item = item.asdict()
    else:
        item.update(response.asdict())
    return jsonify(item), 200, add_custom_headers()

def make_fault_response(ex, rc = 500, message = "Exception"):
    response = models.Response(state.hostname, rc, message, str(ex), (time() - g.begin) * 1000)
    return jsonify(response.asdict()), rc, add_custom_headers()

def add_custom_headers(headers = {}):
    """routine to inject our timer header"""
    headers['X-Timer'] = "%0.3f ms" % ((time() - g.begin) * 1000)
    return headers
