from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from plots import report_status, gen_id
import os, subprocess, psutil

engine = create_engine("sqlite:////Users/zacharyandalman/PycharmProjects/analysis/data.db", convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    Base.metadata.create_all(bind=engine)

def get_routines(**kwargs):
    res = Routine.query
    for key, value in kwargs.items():
        res = res.filter(getattr(Routine, key) == value)
    return res.first()

def routine_names():
    for routine in Routine.query.all():
        yield routine.name

class Routine(Base):

    __tablename__ = "routines"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    path = Column(String, unique=True)
    file_id = Column(String, unique=True)
    running = Column(Boolean)
    pid = Column(Integer, unique=True)

    def __init__(self, folder, filename):
        self.name = filename
        self.path = os.path.join(folder, filename)
        self.file_id = gen_id("f", filename)
        self.running = False
        self.pid = None

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