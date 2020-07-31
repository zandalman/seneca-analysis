from flask_sqlalchemy import SQLAlchemy
import os, html, subprocess, psutil, datetime
from plots import gen_id

db = SQLAlchemy()


def get_objects(obj, count=False, **kwargs):
    """
    Retrieve objects from the database using SQLAlchemy.

    Args:
        obj: The class of objects to retrieve.
        count (bool): If True, returns the number of objects rather than the objects themselves.
        **kwargs: Attribute filters for the database query.

    Returns:
        If count is True, returns the number of objects from the database query.
        Otherwise, returns a list of objects from the database query.
    """
    res = obj.query
    for key, value in kwargs.items():
        res = res.filter(getattr(obj, key) == value)
    if count:
        return res.count()
    else:
        return res.all()


def report_status(obj_response, container_id, msg):
    """
    Send a message to an HTML element and log the message in the log file.

    Args:
        obj_response: Sijax object response.
        container_id (str): The id of the container for the message.
        msg (str): The message to send.
    """
    if obj_response is not None:
        obj_response.html_append("#%s" % container_id, "%s<br/>" % html.escape(msg))
    log_path = get_objects(Misc)[0].log_path
    if log_path:
        with open(log_path, "a+") as f:
            f.write("%s -- %s\n" % (datetime.datetime.utcnow().strftime("%m/%d/%Y %H:%M:%S.%f"), msg))


class Routine(db.Model):
    """
    SQLAlchemy model for storing routines in the database.

    Args:
        folder (str): The path to the directory containing the routine file.
        filename (str): The name of the routine file.

    Attributes:
        id (int): The unique id for the routine in the database.
        name (str): The name of the routine.
        path (str): The path to the routine.
        file_id (str): An id to associate with the routine in the analysis app.
        running (bool): Whether the routine is running. True even if the routine is paused.
        pid (int): The process id associated with the running routine process.
        process: A psutil.Process object associated with the running routine process.
    """
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
        """
        Report the result of a routine after it has completed.

        Args:
            obj_response: Sijax object response.
            stdout: The standard output from the routine.
        """
        if "Error" in stdout.decode("utf-8"):
            obj_response.call("adjust_routine_class", [self.file_id, "error"])
            report_status(obj_response, "status", "'%s' error: '%s'." % (self.name, stdout.decode("utf-8")))
        else:
            obj_response.call("adjust_routine_class", [self.file_id, None])
            report_status(obj_response, "status", "'%s' completed successfully." % self.name)

    def stop(self, obj_response):
        """
        Stop the routine.

        Args:
            obj_response: Sijax object response.
        """
        self.running = False
        self.process.terminate()
        self.process.kill()
        obj_response.call("adjust_routine_class", [self.file_id, None])
        report_status(obj_response, "status", "'%s' terminated successfully." % self.name)

    def pause(self, obj_response):
        """
        Pause the routine.

        Args:
            obj_response: Sijax object response.
        """
        self.process.suspend()
        obj_response.call("adjust_routine_class", [self.file_id, "paused"])
        report_status(obj_response, "status", "'%s' paused." % self.name)

    def resume(self, obj_response):
        """
        Resume the routine after being paused.

        obj_response: Sijax object response.
        """
        self.process.resume()
        report_status(obj_response, "status", "'%s' resumed." % self.name)

    def start(self):
        """
        Start the routine.

        Returns:
             subprocess.pOpen object associated with the running routine process.
        """
        p = subprocess.Popen(["python", self.path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.pid = p.pid
        self.running = True
        report_status(None, "status", "Running '%s'." % self.name)
        return p

    @property
    def process(self):
        if self.pid:
            return psutil.Process(self.pid)


class Misc(db.Model):
    """
    SQLAlchemy model for storing miscellaneous data in the database.

    Attributes:
        log_path (str): The log file path.
    """
    id = db.Column(db.Integer, primary_key=True)
    log_path = db.Column(db.String)

    def __init__(self):
        self.log_path = None
