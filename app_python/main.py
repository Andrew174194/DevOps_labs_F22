from flask import Flask, Blueprint, request, Response
from multiprocessing import Process
from datetime import datetime
from zoneinfo import ZoneInfo
from sys import version_info

# for metrics
from prometheus_client import Counter, Histogram, generate_latest
CONTENT_TYPE = str('text/plain; version=0.0.4; charset=utf-8')
REQUEST_COUNT = Counter(
    'request_count', 'App Request Count',
    ['app_name', 'method', 'endpoint', 'http_status']
)

bp = Blueprint('app', __name__)

@bp.route('/')
def main():
    time_msc = datetime.now(ZoneInfo("Europe/Moscow")).time()
    time_text = time_msc.isoformat(timespec='seconds')
    
    write_log = Process(target=saveLog, args=(f"{time_text} - {request.remote_addr}\n",), daemon=True)
    write_log.start()

    return ("Moscow time: " +
        time_text +
        "<br><br>(the time is actual for the last webpage load)")

def saveLog(log_str):
    with open("/app/visits/visits.txt", "a+") as fo:
        fo.write(log_str)

@bp.route('/visits')
def visits():
    web_content = "History of visits at timestamps and requester's IP:<br>"

    try:
        with open("/app/visits/visits.txt", "r") as fo:   
            file_text = fo.read().replace('\n', '<br>')
            web_content += f"{file_text}"
    except FileNotFoundError:
        pass

    return web_content


@bp.route('/metrics')
def stats():
    return Response(generate_latest(), mimetype=CONTENT_TYPE)

# save metrics to Prometheus Client
def save_metric(response):
    REQUEST_COUNT.labels('py_app', request.method, request.path, response.status_code).inc()
    return response

def create_app(config=None):
    app = Flask(__name__)
    app.register_blueprint(bp)
    app.after_request(save_metric)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0") if version_info >= (3, 9) else \
    print("Error: zoneinfo requires Python 3.9 or newer")