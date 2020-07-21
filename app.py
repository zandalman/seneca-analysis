
# import modules
from flask import Flask, render_template, g
from flask_caching import Cache
import flask_sijax
import time
import numpy as np
from werkzeug import secure_filename
from database import *
from plots import *

# initialize and configure Flask
app = Flask(__name__)
sijax_path = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')
app.config.update(
    SIJAX_STATIC_PATH=sijax_path,
    SIJAX_JSON_URI='/static/js/sijax/json2.js',
    UPLOAD_FOLDER=os.path.join(app.root_path, "uploads"),
    CACHE_TYPE="simple",
    CACHE_DEFAULT_TIMEOUT=999999999,
    CACHE_THRESHOLD=999999999
)
flask_sijax.Sijax(app)
cache = Cache(app)
# initialize database
init_db()


# set global variables
PLOT_DATA_PATH = os.path.join(app.root_path, "plot_data")
ROUTINES_PATH = os.path.join(app.root_path, "routines")


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


# do one analysis iteration
def analysis_step(obj_response):
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
                    if obj.id not in [plot["id"] for plot in cache.get("current_plots")]:
                        if not obj.file in [plot["file"] for plot in cache.get("current_plots")]: # Check if data is from a new routine
                            report_status(obj_response, "status", "Receiving data from '%s'." % obj.file)
                            yield from obj.create_routine(obj_response)
                        yield from obj.create(obj_response)
                        cache.set("current_plots", cache.get("current_plots") + [dict(file=obj.file, id=obj.id)])
                    else:
                        yield from obj.update(obj_response)


def add_routine(obj_response, files, form_values):
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
    elif filename in routine_names():
        report_status(obj_response, "status", "A routine with the name '%s' already exists." % filename)
    else:
        routine = Routine(app.config["UPLOAD_FOLDER"], filename)
        db_session.add(routine)
        db_session.commit()
        file_data.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        obj_response.html_append("#routine-list", "<li class='routine' id='%s'>%s</li>" % (routine.file_id, filename))
        report_status(obj_response, "status", "Upload of '%s' successful." % filename)


class SijaxHandlers(object):

    @staticmethod
    def stop_analysis(obj_response):
        """Stop the analysis."""
        cache.set("analysis_on", False)
        report_status(obj_response, "status", "Analysis stopped")
        obj_response.call("reset_timer")

    @staticmethod
    def pause_analysis(obj_response):
        """Pause the analysis."""
        cache.set("analysis_on", False)
        report_status(obj_response, "status", "Analysis paused")
        obj_response.call("stop_timer")

    @staticmethod
    def remove_routine(obj_response, file_ids):
        filenames = []
        for file_id in file_ids:
            routine = get_routines(file_id=file_id)
            filename = routine.name
            filenames.append(filename)
            try:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            except FileNotFoundError:
                report_status(obj_response, "status", "Unable to locate '%s'." % filename)
            db_session.delete(routine)
        if len(file_ids) > 3:
            report_status(obj_response, "status", "%s routines removed." % len(file_ids))
        else:
            report_status(obj_response, "status", "'%s' removed." % "', '".join(filenames))
        db_session.commit()

    @staticmethod
    def stop_routine(obj_response, file_ids):
        for file_id in file_ids:
            routine = get_routines(file_id=file_id)
            if routine.running:
                routine.stop(obj_response)
        db_session.commit()

    @staticmethod
    def run_routine(obj_response, file_id):
        routine = get_routines(file_id=file_id)
        p = routine.start()
        db_session.commit()
        p.wait()
        if routine.running:
            stdout, stderr = p.communicate()
            routine.running = False
            routine.report(obj_response, stdout)
        db_session.commit()

class SijaxCometHandlers(object):

    @staticmethod
    def analyse(obj_response, paused, period):
        """Start the analysis."""
        cache.set("analysis_on", True)
        if paused:
            report_status(obj_response, "status", "Analysis restarted")
        else:
            report_status(obj_response, "status", "Analysis started")
            remove_plots(obj_response)
            cache.set("current_plots", [])
            for plot_data_file in os.listdir(PLOT_DATA_PATH):
                os.remove(os.path.join(PLOT_DATA_PATH, plot_data_file))
        obj_response.call("start_timer") # start the timer
        yield obj_response
        give_warning = True
        while cache.get("analysis_on"):
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
    filenames = os.listdir(app.config["UPLOAD_FOLDER"])
    routines_dict = {}
    for filename in filenames:
        if get_routines(name=filename) is None:
            routine = Routine(app.config["UPLOAD_FOLDER"], filename)
            db_session.add(routine)
        else:
            routine = get_routines(name=filename)
        routines_dict[routine.file_id] = routine.name
    db_session.commit()
    cache.set("analysis_on", False)
    # Register Sijax upload handlers
    form_init_js = ''
    form_init_js += g.sijax.register_upload_callback('add-routine-form', add_routine)
    if g.sijax.is_sijax_request:
        g.sijax.register_object(SijaxHandlers) # Register Sijax handlers
        g.sijax.register_comet_object(SijaxCometHandlers) # Register Sijax comet handlers
        return g.sijax.process_request()
    return render_template("main.html", form_init_js=form_init_js, routines=routines_dict) # Render template


app.run(threaded=True, debug=True) # run the flask app with threads in debug mode
