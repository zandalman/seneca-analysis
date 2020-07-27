from flask_sqlalchemy import SQLAlchemy
import os, html, subprocess, psutil
from plots import gen_id

db = SQLAlchemy()


def get_objects(obj, count=False, **kwargs):
    res = obj.query
    for key, value in kwargs.items():
        res = res.filter(getattr(obj, key) == value)
    if count:
        return res.count()
    else:
        return res.all()


def report_status(obj_response, container_id, msg):
    """Send a message to an HTML element."""
    obj_response.html_append("#%s" % container_id, "%s<br/>" % html.escape(msg))
    log_path = get_objects(Misc)[0].log_path
    if log_path:
        with open(log_path, "a+") as f:
            f.write(msg + "\n")


def routine_names():
    for routine in Routine.query.all():
        yield routine.name


class Routine(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    path = db.Column(db.String)
    file_id = db.Column(db.String)
    running = db.Column(db.Boolean)
    pid = db.Column(db.Integer)

    def __init__(self, folder, filename):
        self.name = filename
        self.path = os.path.join(folder, filename)
        self.file_id = gen_id("f", filename)
        self.running = False
        self.pid = 0

    def report(self, obj_response, stdout):
        if "Error" in stdout.decode("utf-8"):
            obj_response.call("adjust_routine_class", [self.file_id, "error"])
            report_status(obj_response, "status", "'%s' error: '%s'." % (self.name, stdout.decode("utf-8")))
        else:
            obj_response.call("adjust_routine_class", [self.file_id, None])
            report_status(obj_response, "status", "'%s' completed successfully." % self.name)

    def stop(self, obj_response):
        self.running = False
        self.process.terminate()
        self.process.kill()
        obj_response.call("adjust_routine_class", [self.file_id, None])
        report_status(obj_response, "status", "'%s' terminated successfully." % self.name)

    def pause(self, obj_response):
        self.process.suspend()
        obj_response.call("adjust_routine_class", [self.file_id, "paused"])
        report_status(obj_response, "status", "'%s' paused." % self.name)

    def resume(self, obj_response):
        self.process.resume()
        obj_response.call("adjust_routine_class", [self.file_id, "running"])
        report_status(obj_response, "status", "'%s' resumed." % self.name)

    def start(self):
        p = subprocess.Popen(["python", self.path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.pid = p.pid
        self.running = True
        return p

    @property
    def process(self):
        if self.pid:
            return psutil.Process(self.pid)


class Misc(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    log_path = db.Column(db.String)

    def __init__(self):
        self.log_path = None
