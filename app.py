
# import modules
from flask import Flask, render_template, g
import flask_sijax
import os
import time
import numpy as np
import json
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
PLOT_DATA_PATH = os.path.join(app.root_path, "plot_data", "plot_data")
INFO_PER_DUMP = 7
STATIC_INFO_PER_DUMP = 5
analysis_on = False
current_plots = []


# send a message to an html element
def report_status(obj_response, container_id, msg):
    obj_response.html_append("#%s" % container_id, "%s<br/>" % msg)


# remove duplicate plots
def remove_duplicate_plots(plot_data_list):
    plot_data_list_reversed = plot_data_list[::-1]
    for i in reversed(range(len(plot_data_list))):
        if plot_data_list_reversed[i][:STATIC_INFO_PER_DUMP] in [plot[:STATIC_INFO_PER_DUMP] for plot in plot_data_list_reversed[:i]]:
            del plot_data_list_reversed[i]
    return plot_data_list_reversed[::-1]


# do one analysis iteration
def analysis_step(obj_response):
    global current_plots
    if os.path.getsize(PLOT_DATA_PATH) > 0:
        with open(PLOT_DATA_PATH, "r+") as plot_data_file:
            plot_data_list = plot_data_file.read().split("@@@")[1:]
            plot_data_file.truncate(0)
        plot_data_list = np.reshape(plot_data_list, (int(len(plot_data_list) / INFO_PER_DUMP), INFO_PER_DUMP)).tolist()
        plot_data_list = remove_duplicate_plots(plot_data_list)
        for plot_data in plot_data_list:
            plot = dict(type=plot_data[0] ,file=plot_data[1], name=plot_data[2], description=plot_data[3], counter=int(plot_data[4]), url="data:image/png;base64,%s" % plot_data[5], data=json.loads(plot_data[6]))
            if plot_data[:STATIC_INFO_PER_DUMP] not in current_plots:
                if not plot["file"] in [current_plot[1] for current_plot in current_plots]:
                    yield from create_routine(obj_response, plot["file"])
                yield from create_plot(obj_response, plot)
                current_plots.append(plot_data[:STATIC_INFO_PER_DUMP])
            else:
                yield from update_plot(obj_response, plot)


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
        # start the timer
        obj_response.call("start_timer")
        yield obj_response
        while analysis_on:
            step_start_time = time.time()
            yield from analysis_step(obj_response)
            step_time = time.time() - step_start_time
            if period > step_time:
                time.sleep(period - step_time)
            else:
                report_status(obj_response, "status", "Warning: period is shorter than execution time by %.3g seconds" % (step_time - period))


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
