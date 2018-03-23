import logging
from flask import Flask, current_app, redirect, request
from urllib.parse import quote_plus
from random import randint

import config

from demo.io import ChecksumWriter, SharedLockingWriter, ExclusiveLockingWriter
from demo import state, client, models
from demo.flask_ext import _init_handlers, plain_response, json_response
from demo.flask_ext.decorators import add_custom_headers

# Used to set the Writer for the write method call
MODE_FACTORY=dict(
    MODE_RW=ExclusiveLockingWriter,
    MODE_RO=SharedLockingWriter,
    MODE_IG=ChecksumWriter
    )

logger = logging.getLogger(__name__)
app = Flask(__name__)
_init_handlers(app)

@app.route("/")
def index():
    return redirect('/api/writer/healthz')

@app.route("/api/writer/healthz")
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

def parse_write_mode(mode):
    if mode not in MODE_FACTORY:
        raise ValueError("Passed mode parameter not in list: %s" % MODE_FACTORY.keys())
    factory = MODE_FACTORY[mode]
    return factory

def parse_write_data():
    data = request.args.get('data', None)
    if data is not None:
        return data
    return "Sample Data %x" % randint(0x1000, 0xffff)

@app.route("/api/writer/write/<int:entries>/<mode>/<int:level>")
@app.route("/api/writer/write/<int:entries>/<mode>")
@app.route("/api/writer/write/<int:entries>")
@app.route("/api/writer/write")
@json_response
def write(entries = 1, mode = 'MODE_RW', level = 0, data = None):
    factory = parse_write_mode(mode)
    assert issubclass(factory, ChecksumWriter)

    data = parse_write_data()

    entries = entries if entries <= 1024 else 1024;

    with factory(state.DEMO_FILE_PATH, demo_level = level) as rw:
        written = models.Writes(0, entries)
        for e in range(entries):
            seq = getattr(state.threaded, 'seq', 0)
            seq += 1
            state.threaded.seq = seq
            written.bytes += rw.write("[%d] %s" % (seq, data)).bytes
        ret = models.WritesResponse(written)

        return ret

@app.route("/api/writer/truncate")
@json_response
def truncate():
    with ExclusiveLockingWriter(state.DEMO_FILE_PATH) as rw:
        rw.truncate()
    return models.TruncatedResponse('File Truncated', state.DEMO_FILE_PATH, True)

@app.route("/api/writer/pods")
@app.route("/api/writer/pods/")
@json_response
def pods():
    records = client.get_my_pods()
    return models.PodListResponse(records)

@app.route("/api/writer/stream/pods")
@app.route("/api/writer/stream/pods/")
def stream_pods():
    generator = client.generator_my_pods_watch()
    return current_app.response_class(
        generator,
        200,
        mimetype='text/event-stream',
        headers=add_custom_headers())

def call_client_pod(pod_name, path):
    remote = client.get_url_from_pod(pod_name, path)
    ret = models.RemoteResponse(remote)
    return ret

@app.route("/api/writer/pods/<pod_name>/write/<int:entries>/<mode>/<int:level>")
@app.route("/api/writer/pods/<pod_name>/write/<int:entries>/<mode>")
@app.route("/api/writer/pods/<pod_name>/write/<int:entries>")
@app.route("/api/writer/pods/<pod_name>/write")
@json_response
def pod_write(pod_name, entries = 1, mode = 'MODE_RW', level = 0, data = None):
    parse_write_mode(mode)
    data = parse_write_data()
    path = "/api/writer/write/%d/%s/%d?data=%s" % (entries, mode, level, quote_plus(data))

    return call_client_pod(pod_name, path)

@app.route("/api/writer/pods/<pod_name>/truncate")
@json_response
def pod_truncate(pod_name):
    path = "/api/writer/truncate"
    return call_client_pod(pod_name, path)

if __name__ == "__main__":
    app.run()
