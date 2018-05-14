import logging
from time import time
from flask import Flask, g, request, current_app, redirect
from itsdangerous import json

from demo.io import SharedLockingWriter
from demo import state, client, models
from demo.flask_ext import _init_handlers, plain_response, json_response, stream_response
from demo.flask_ext.decorators import add_custom_headers

logger = logging.getLogger(__name__)
app = Flask(__name__)
_init_handlers(app)

@app.route("/api/reader")
@app.route("/api/reader/")
def index():
    return redirect('/api/reader/read')

@app.route("/api/reader/healthz")
@plain_response()
def healthz():
    errors = [];
    try:
        open(state.DEMO_FILE_PATH, "a+").close();
    except IOError as ex:
        logger.exception('Unable to read pods')
        errors.append(str(ex))
    try:
        pods = client.nocache_get_my_pods();
        if pods.num < 1:
            raise ValueError('no pods were returned!')
    except Exception as ex:
        logger.exception('unable to access db file')
        errors.append(str(ex))
    return "ok" if not errors else str(errors)

@app.route("/api/reader/read")
@app.route("/api/reader/read/<int:pos>")
@json_response
def read_wrapper(pos = -1, summary = None):
    if summary is None:
        summary = request.args.get('summary', None)
        summary = False if summary is None else True
    if pos < 1:
        pos = getattr(g, 'stream_tracker', 0)
    return read(pos, summary)

def read(pos = 0, summary = False):
    with SharedLockingWriter(state.DEMO_FILE_PATH, pos=pos, timeout = state.DEMO_READ_TIMEOUT) as ro:
        good_list = ro.read()
        errors_list = ro.errors
        failed_list = ro.failed_checksum
        read_collection = models.ReadCollection(
            ro.tell(),
            good_list,
            errors_list,
            failed_list)
        if summary:
            read_collection.records.items=[]
            read_collection.errors.items=[]
            read_collection.fails.items=[]
        ret = models.ReadResponse(read_collection)
        state.threaded.pos = ret.reads.pos
        return ret

@app.route("/api/reader/stream/read")
@app.route("/api/reader/stream/read/")
@app.route("/api/reader/stream/read/<int:pos>")
@stream_response(timeout = 60)
def stream_read(pos = -1, summary = None):
    if summary is None:
        summary = request.args.get('summary', None)
        summary = False if summary is None else True

    # if stream_tracker exists, then we're in a 2nd call of the same request.
    pos = getattr(g, 'stream_tracker', pos)

    if pos < 1:
        pos = 0

    item = read(pos, summary)
    g.stream_tracker = item.reads.pos

    response = models.Response(state.hostname, 200, 'Ok', None, (time() - g.begin) * 1000)
    if isinstance(item, models.LazyResponse):
        item.add_response(response)
    if isinstance(item, models.Model):
        item = item.asdict()
    else:
        item.update(response.asdict())
    return json.dumps(item)

@app.route("/api/reader/pods")
@app.route("/api/reader/pods/")
@json_response
def pods():
    records = client.get_my_pods()
    return models.PodListResponse(records)

@app.route("/api/reader/stream/pods")
@app.route("/api/reader/stream/pods/")
def stream_pods():
    generator = client.generator_my_pods_watch()
    return current_app.response_class(
        generator,
        200,
        mimetype='text/event-stream',
        headers=add_custom_headers())

@app.route("/api/reader/pvcs")
@json_response
def pvcs():
    records = client.get_my_pvcs()
    return models.PvcListResponse(records)

def call_client_pod(pod_name, path):
    remote = client.get_url_from_pod(pod_name, path)
    ret = models.RemoteResponse(remote)
    return ret

@app.route("/api/reader/pods/<pod_name>/read/<int:pos>")
@app.route("/api/reader/pods/<pod_name>/read")
@json_response
def pod_read(pod_name, pos = 0):
    summary = request.args.get('summary', None)
    summary = False if summary is None else True
    path = '/api/reader/read/%d' % pos
    if summary:
        path += '?summary'

    return call_client_pod(pod_name, path)
