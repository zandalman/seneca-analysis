
# import modules
from flask import Flask, render_template, g
import flask_sijax
import os
import time
import numpy as np
from werkzeug import secure_filename
from multiprocessing import Process
from plots import *


# initialize and configure Flask
app = Flask(__name__)
sijax_path = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')
app.config.update(
    SIJAX_STATIC_PATH=sijax_path,
    SIJAX_JSON_URI='/static/js/sijax/json2.js',
    UPLOAD_FOLDER=os.path.join(app.root_path, "uploads")
)
flask_sijax.Sijax(app)


# set global variables
PLOT_DATA_PATH = os.path.join(app.root_path, "plot_data")
ROUTINES_PATH = os.path.join(app.root_path, "routines")
analysis_on = False
current_plots = []
routines = []

def report_status(obj_response, container_id, msg):
    """Send a message to an HTML element."""
    obj_response.html_append("#%s" % container_id, "%s<br/>" % html.escape(msg))


# do one analysis iteration
def analysis_step(obj_response):
    global current_plots
    for plot_data_file in os.listdir(PLOT_DATA_PATH):
        plot_data_file_path = os.path.join(PLOT_DATA_PATH, plot_data_file)
        if os.path.getsize(plot_data_file_path) > 0:  # ignore empty files
            try:
                plot_data_list = np.load(plot_data_file_path, allow_pickle=True)  # load the data
            except Exception:
                break
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
                        if not obj.file in [plot["file"] for plot in current_plots]: # Check if data is from a new routine
                            report_status(obj_response, "status", "Receiving data from '%s'." % obj.file)
                            yield from obj.create_routine(obj_response)
                        yield from obj.create(obj_response)
                        current_plots.append(dict(file=obj.file, id=obj.id))
                    else:
                        yield from obj.update(obj_response)


def add_routine(obj_response, files, form_values):
    global routines
    if "routine" not in files:
        report_status(obj_response, "status", "Upload unsuccessful.")
        return
    file_data = files['routine']
    filename = file_data.filename
    if not filename:
        report_status(obj_response, "status", "Upload cancelled.")
    elif "python" not in file_data.content_type:
        report_status(obj_response, "status", "'%s' is not a Python script." % filename)
    elif filename != secure_filename(filename):
        report_status(obj_response, "status", "File name '%s' is not secure." % filename)
    elif filename in [routine.name for routine in routines]:
        report_status(obj_response, "status", "A routine with the name '%s' already exists." % filename)
    else:
        routines.append(Routine(filename))
        file_data.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        obj_response.html_append("#routine-list", "<li class='routine' id='%s'>%s</li>" % (routines[-1].id, filename))
        report_status(obj_response, "status", "Upload of '%s' successful." % filename)


class Routine(object):

    def __init__(self, filename):
        self.name = filename
        self.path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        self.id = gen_id("f", filename)
        self.running = False

    def run(self, obj_response):
        self.process = subprocess.Popen(["python", self.path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        obj_response.attr("#%s" % self.id, "class", "routine ui-selectee ui-selected running")
        report_status(obj_response, "status", "Running '%s'." % self.name)
        yield obj_response
        while self.running and self.process.poll() is None:
            time.sleep(1)
        else:
            stdout, stderr = self.process.communicate()
            if stderr:
                obj_response.attr("#%s" % self.id, "class", "routine ui-selectee error")
                report_status(obj_response, "status", "'%s' error: '%s'." % self.name, stderr)
            else:
                obj_response.attr("#%s" % self.id, "class", "routine ui-selectee")
                report_status(obj_response, "status", "'%s' completed successfully." % self.name)
            self.running = False
            yield obj_response

    def stop(self, obj_response):
        self.process.terminate()
        obj_response.attr("#%s" % self.id, "class", "routine ui-selectee")
        report_status(obj_response, "status", "'%s' terminated successfully." % self.name)

class SijaxHandlers(object):

    @staticmethod
    def stop_analysis(obj_response):
        """Stop the analysis."""
        global analysis_on
        analysis_on = False
        report_status(obj_response, "status", "Analysis stopped")
        obj_response.call("reset_timer")

    @staticmethod
    def pause_analysis(obj_response):
        """Pause the analysis."""
        global analysis_on
        analysis_on = False
        report_status(obj_response, "status", "Analysis paused")
        obj_response.call("stop_timer")

    @staticmethod
    def remove_routine(obj_response, file_ids):
        global routines
        filenames = []
        for file_id in file_ids:
            routine = [routine for routine in routines if routine.id == file_id][0]
            filename = routine.name
            filenames.append(filename)
            try:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            except FileNotFoundError:
                report_status(obj_response, "status", "Unable to locate '%s'." % filename)
            routines = [routine for routine in routines if routine.id != file_id]
        if len(file_ids) > 3:
            report_status(obj_response, "status", "%s routines removed." % len(file_ids))
        else:
            report_status(obj_response, "status", "%s removed." % ", ".join(filenames))

    @staticmethod
    def stop_routine(obj_response, file_ids):
        global routines
        for file_id in file_ids:
            routine = [routine for routine in routines if routine.id == file_id][0]
            if routine.running:
                print("test")
                routine.stop()

class SijaxCometHandlers(object):

    @staticmethod
    def run_routine(obj_response, file_id):
        global routines
        routine = [routine for routine in routines if routine.id == file_id][0]
        yield from routine.run(obj_response)

    @staticmethod
    def analyse(obj_response, paused, period):
        """Start the analysis."""
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
        obj_response.call("start_timer") # start the timer
        yield obj_response
        give_warning = True
        while analysis_on:
            step_start_time = time.time()
            yield from analysis_step(obj_response)
            step_time = time.time() - step_start_time
            if period > step_time:
                time.sleep(period - step_time)
            else:
                if give_warning: # Check if warning has already been given for this routine
                    report_status(obj_response, "status", "Warning: Period is shorter than execution time by %.3g seconds" % (step_time - period))
                    give_warning = False


@flask_sijax.route(app, '/')
def main():
    """Generate the main page."""
    global routines
    filenames = os.listdir(app.config["UPLOAD_FOLDER"])
    routines = [Routine(filename) for filename in filenames]
    routines_dict = {routine.id: routine.name for routine in routines}
    # Register Sijax upload handlers
    form_init_js = ''
    form_init_js += g.sijax.register_upload_callback('add-routine-form', add_routine)
    if g.sijax.is_sijax_request:
        g.sijax.register_object(SijaxHandlers) # Register Sijax handlers
        g.sijax.register_comet_object(SijaxCometHandlers) # Register Sijax comet handlers
        return g.sijax.process_request()
    return render_template('main.html', form_init_js=form_init_js, routines=routines_dict) # Render template


app.run(threaded=True, debug=True) # run the flask app with threads in debug mode
