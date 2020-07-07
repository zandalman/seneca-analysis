
# import modules
from flask import Flask, render_template, g
import os, sys
import flask_sijax
from werkzeug import secure_filename
import json
import inspect
import importlib
import time
import re
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from plots import *

observer_container = []

# initialize and configure Flask
app = Flask(__name__)
sijax_path = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')
app.config.update(
    SIJAX_STATIC_PATH=sijax_path,
    SIJAX_JSON_URI='/static/js/sijax/json2.js'
)
flask_sijax.Sijax(app)
# set global variables
analysis_on = False

# send a message to an html element
def report_status(obj_response, container_id, msg):
    obj_response.html_append("#%s" % container_id, "%s<br/>" % msg)

def format_time(seconds):
    if seconds > 86400:
        return "%.3g days" % (seconds / 86400)
    elif seconds > 3600:
        return "%.3g hours" % (seconds / 3600)
    elif seconds > 60:
        return "%.3g minutes" % (seconds / 60)
    elif seconds < .001:
        return "0 seconds"
    else:
        return "%.3g seconds" % seconds

class WatchDogHandler(PatternMatchingEventHandler):

    def on_modified(self, event):
        plot_data_path = os.path.join(app.root_path, "plot_data", "plot_data.txt")
        with open(plot_data_path, 'r') as plot_data:
            plot_data.read(plot_data)


class SijaxHandlers(object):

    # stop the analysis
    @staticmethod
    def stop_analysis(obj_response):
        global analysis_on
        analysis_on = False
        report_status(obj_response, "status", "Analysis stopped")
        obj_response.call("reset_timer")

    # pause the analysis
    @staticmethod
    def pause_analysis(obj_response):
        global analysis_on
        analysis_on = False
        report_status(obj_response, "status", "Analysis paused")
        obj_response.call("stop_timer")

    # start the analysis
    @staticmethod
    def analyse(obj_response, paused, data={}):
        global analysis_on, observer_container
        analysis_on = True
        # remove all plots if not paused
        if not paused:
            remove_plots(obj_response)

        if paused:
            report_status(obj_response, "status", "Analysis restarted")
        else:
            report_status(obj_response, "status", "Analysis started")
        # start the timer
        obj_response.call("start_timer")

class SijaxCometHandlers(object):

    # periodically update the plot and data tables for a routine
    @staticmethod
    def analyse_routine(obj_response, data_dir, routine, period):
        new_analysis = routine["analysis"]["new"]
        if new_analysis:
            yield from analyse_routine_new(obj_response, data_dir, routine, period)
        else:
            yield from analyse_routine_old(obj_response, data_dir, routine, period)

# route the plot page
@flask_sijax.route(app, '/')
def main_plot():

    if g.sijax.is_sijax_request:
        # register Sijax handlers
        g.sijax.register_object(SijaxHandlers)
        # register Sijax comet handlers
        g.sijax.register_comet_object(SijaxCometHandlers)
        return g.sijax.process_request()
    # render template
    return render_template('plot.html')


# run the flask app with threads in debug mode
app.run(threaded=True, debug=True)