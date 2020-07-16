
# import modules
from flask import Flask, render_template, g
import flask_sijax
import os
import time
import numpy as np
from werkzeug import secure_filename
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
ROUTINES_PATH = os.path.join(app.root_path, "routines")
analysis_on = False
current_plots = []
file_order = []


def report_status(obj_response, container_id, msg):
    """Send a message to an HTML element."""
    obj_response.html_append("#%s" % container_id, "%s<br/>" % html.escape(msg))


# do one analysis iteration
def analysis_step(obj_response):
    global current_plots
    for plot_data_file in os.listdir(PLOT_DATA_PATH):
        plot_data_file_path = os.path.join(PLOT_DATA_PATH, plot_data_file)
        if os.path.getsize(plot_data_file_path) > 0: # ignore empty files
            try:
                plot_data_list = np.load(plot_data_file_path, allow_pickle=True) # load the data
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


def remove_lines(file, lines_to_remove):
    with open(file, "r") as f:
        lines = f.readlines()
    with open(file, "w") as f:
        for line in lines:
            if line.strip("\n") not in lines_to_remove:
                f.write(line)


def add_line(file, line):
    with open(file, "a") as f:
        f.write(line + "\n")


def add_routine(obj_response, files, form_values):
    global file_order
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
    elif filename in file_order:
        report_status(obj_response, "status", "A routine with the name '%s' already exists." % filename)
    else:
        report_status(obj_response, "status", "Upload of '%s' successful." % filename)
        obj_response.html_append("#routine-list", "<li class='routine' id='f%s'>%s</li>" % (len(file_order), html.escape(filename)))
        add_line(ROUTINES_PATH, filename)
        file_order.append(filename)



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
        global file_order
        file_indices = [int(file_id[1:]) for file_id in file_ids]
        filenames = [file_order[file_index] for file_index in file_indices]
        remove_lines(ROUTINES_PATH, filenames)
        file_order = [filename for i, filename in enumerate(file_order) if i not in frozenset(file_indices)]
        if len(filenames) > 3:
            report_status(obj_response, "status", "%s routines removed." % len(filenames))
        else:
            report_status(obj_response, "status", "%s removed." % ", ".join(filenames))

class SijaxCometHandlers(object):

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
    global file_order
    with open(ROUTINES_PATH, "r") as f:
        filenames = [filename.strip("\n") for filename in f.readlines()]
    file_order = filenames
    # Register Sijax upload handlers
    form_init_js = ''
    form_init_js += g.sijax.register_upload_callback('add-routine-form', add_routine)
    if g.sijax.is_sijax_request:
        g.sijax.register_object(SijaxHandlers) # Register Sijax handlers
        g.sijax.register_comet_object(SijaxCometHandlers) # Register Sijax comet handlers
        return g.sijax.process_request()
    return render_template('main.html', form_init_js=form_init_js, filenames=[html.escape(filename) for filename in filenames]) # Render template


app.run(threaded=True, debug=True) # run the flask app with threads in debug mode
