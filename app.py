
# import modules
from flask import Flask, render_template, g
import flask_sijax
import os
import time
import numpy as np
from plots import *


# initialize and configure Flask
app = Flask(__name__)
sijax_path = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')
app.config.update(
    SIJAX_STATIC_PATH=sijax_path,
    SIJAX_JSON_URI='/static/js/sijax/json2.js'
)
flask_sijax.Sijax(app)


# set global variables
PLOT_DATA_PATH = os.path.join(app.root_path, "plot_data")
analysis_on = False
current_plots = []


# send a message to an html element
def report_status(obj_response, container_id, msg):
    obj_response.html_append("#%s" % container_id, "%s<br/>" % html.escape(msg))


# do one analysis iteration
def analysis_step(obj_response):
    global current_plots
    for plot_data_file in os.listdir(PLOT_DATA_PATH):
        plot_data_file_path = os.path.join(PLOT_DATA_PATH, plot_data_file)
        if os.path.getsize(plot_data_file_path) > 0:
            plot_data_list = np.load(plot_data_file_path, allow_pickle=True)
            for plot_data in plot_data_list:
                if plot_data["type"] == "message":
                    report_status(obj_response, "status", "'%s': %s" % (plot_data["file"], plot_data["message"]))
                    yield obj_response
                elif plot_data["type"] == "complete":
                    report_status(obj_response, "status", "'%s': Analysis complete!" % plot_data["file"])
                    os.remove(os.path.join(PLOT_DATA_PATH, "%s.npy" % os.path.splitext(plot_data["file"])[0]))
                    yield obj_response
                else:
                    obj = obj_types[plot_data["type"]](plot_data)
                    if obj.id not in [plot["id"] for plot in current_plots]:
                        if not obj.file in [plot["file"] for plot in current_plots]:
                            report_status(obj_response, "status", "Receiving data from '%s'." % obj.file)
                            yield from obj.create_routine(obj_response)
                        yield from obj.create(obj_response)
                        current_plots.append(dict(file=obj.file, id=obj.id))
                    else:
                        yield from obj.update(obj_response)

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


class SijaxCometHandlers(object):

    # start the analysis
    @staticmethod
    def analyse(obj_response, paused, period):
        global analysis_on, current_plots
        analysis_on = True
        if paused:
            report_status(obj_response, "status", "Analysis restarted")
        else:
            report_status(obj_response, "status", "Analysis started")
            remove_plots(obj_response)
            current_plots = []
            for plot_data_file in os.listdir(PLOT_DATA_PATH):
                os.remove(os.path.join(PLOT_DATA_PATH, plot_data_file))
        # start the timer
        obj_response.call("start_timer")
        yield obj_response
        give_warning = True
        while analysis_on:
            step_start_time = time.time()
            yield from analysis_step(obj_response)
            step_time = time.time() - step_start_time
            if period > step_time:
                time.sleep(period - step_time)
            else:
                if give_warning:
                    report_status(obj_response, "status", "Warning: Period is shorter than execution time by %.3g seconds" % (step_time - period))
                    give_warning = False


# route the plot page
@flask_sijax.route(app, '/')
def main():

    if g.sijax.is_sijax_request:
        g.sijax.register_object(SijaxHandlers) # register Sijax handlers
        g.sijax.register_comet_object(SijaxCometHandlers) # register Sijax comet handlers
        return g.sijax.process_request()
    return render_template('main.html') # render template


# run the flask app with threads in debug mode
app.run(threaded=True, debug=True)
