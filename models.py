from flask_sqlalchemy import SQLAlchemy
import psutil
import subprocess
import os
from plots import report_status, gen_id

db = SQLAlchemy()


def get_routines(**kwargs):
    res = Routine.query
    for key, value in kwargs.items():
        res = res.filter(getattr(Routine, key) == value)
    return res.first()


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
            obj_response.call("adjust_routine_class", [self.file_id, True])
            report_status(obj_response, "status", "'%s' error: '%s'." % (self.name, stdout.decode("utf-8")))
        else:
            obj_response.call("adjust_routine_class", [self.file_id, False])
            report_status(obj_response, "status", "'%s' completed successfully." % self.name)

    def stop(self, obj_response):
        self.running = False
        self.process.terminate()
        self.process.kill()
        obj_response.call("adjust_routine_class", [self.file_id, False])
        report_status(obj_response, "status", "'%s' terminated successfully." % self.name)

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
    analysis_on = db.Column(db.Boolean)
    current_plots = db.Column(db.JSON)

    def __init__(self):
        self.analysis_on = False
        self.current_plots = []



