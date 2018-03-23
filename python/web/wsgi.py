import logging
from flask import Flask, render_template, current_app, redirect, url_for

import config

from demo import state, models, client, EnvState
from demo.flask_ext import _init_handlers, json_response
from demo.flask_ext.decorators import add_custom_headers


logger = logging.getLogger(__name__)
app = Flask(__name__)
_init_handlers(app)

@app.route("/")
def index():
    return render_template('index.html', name=state.NAME)

@app.route("/swagger.yaml")
def swagger_yaml():
    swagger = EnvState()
    swagger.fromenv('ROUTE_HOSTNAME', 'test.example.com')
    return render_template('swagger.yaml', ROUTE_HOSTNAME=swagger.ROUTE_HOSTNAME)

@app.route("/docs")
@app.route("/docs/")
def swagger_docs():
    return redirect('/static/docs/index.html')

@app.route("/api/web/pods")
@app.route("/api/web/pods/")
@json_response
def pods():
    records = client.get_my_pods()
    return models.PodListResponse(records)

@app.route("/api/web/stream/pods")
@app.route("/api/web/stream/pods/")
def stream_pods():
    generator = client.generator_my_pods_watch()
    return current_app.response_class(
        generator,
        200,
        mimetype='text/event-stream',
        headers=add_custom_headers())

if __name__ == "__main__":
    app.run()
