
# import modules
import numpy as np
import time
from werkzeug import secure_filename
from plots import *
from models import *


# define global variables
analysis_on = False


class Analysis(object):
    """
    Analysis object encapsulating all analysis methods.

    Analysis objects are instantiated by SijaxCometHandlers.analyse.

    Args:
        app: The flask app.
        paused (bool): Whether the analysis is paused.
        period (float): The analysis period.
        plots (list): A list of dictionaries corresponding to currently active plots.
                Each dictionary contains the ids associated with the plot and its file.

    Attributes:
        app: The flask app.
        paused (bool): Whether the analysis is paused.
        period (float): The analysis period.
        plots (list): The current plots in the analysis.
        warn (bool): Give an execution time warning.
        start_time (float): The start time of the analysis.
    """
    def __init__(self, app, paused, period, plots):
        global analysis_on
        self.app = app
        self.paused = paused
        self.period = period
        if self.paused:
            self.plots = plots
        else:
            self.plots = []
        self.warn = True
        self.start_time = time.time()
        analysis_on = True

    def start(self, obj_response):
        """
        Start the analysis.

        Args:
            obj_response: Sijax object response

        Yields:
            The updated Sijax object response.
        """
        if self.paused:
            report_status(obj_response, "status", "Analysis restarted")
        else:
            report_status(obj_response, "status", "Analysis started")
            obj_response.html("#plots-container, #plot-list", "")
            for plot_data_file in os.listdir(self.app.config["PLOT_DATA_FOLDER"]):
                os.remove(os.path.join(self.app.config["PLOT_DATA_FOLDER"], plot_data_file))
        obj_response.call("start_timer") # start the timer
        yield obj_response

    def step(self, obj_response):
        """
        Do one analysis iteration.

        Args:
            obj_response: Sijax object response.
        """
        self.start_time = time.time()
        yield from self.update(obj_response)
        step_time = time.time() - self.start_time
        if self.period > step_time:
            time.sleep(self.period - step_time)
        else:
            if self.warn:  # Check if warning has already been given
                report_status(obj_response, "status", "Warning: Period is shorter than execution time by %.3g seconds" % (step_time - self.period))
                self.warn = False

    def update(self, obj_response):
        """
        Update plot data with latest data from buffer files.

        Args:
            obj_response: Sijax object response.

        Yields:
            The updated Sijax object response.
        """
        for plot_buffer in os.listdir(self.app.config["PLOT_DATA_FOLDER"]):
            plot_buffer_path = os.path.join(self.app.config["PLOT_DATA_FOLDER"], plot_buffer)
            if os.path.getsize(plot_buffer_path) > 0:  # ignore empty files
                try:
                    plot_data_list = np.load(plot_buffer_path, allow_pickle=True)  # load the data
                except Exception:
                    break
                for plot_data in plot_data_list:
                    if plot_data["type"] == "message":
                        report_status(obj_response, "status", "'%s': %s" % (plot_data["file"], plot_data["message"]))
                        yield obj_response
                    elif plot_data["type"] == "complete":
                        report_status(obj_response, "status", "'%s': Analysis complete!" % plot_data["file"])
                        os.remove(os.path.join(self.app.config["PLOT_DATA_FOLDER"], "%s.npy" % os.path.splitext(plot_data["file"])[0]))
                        yield obj_response
                    else:
                        obj = obj_types[plot_data["type"]](plot_data)
                        if obj.id not in [plot["id"] for plot in self.plots]:
                            if obj.routine_list_id not in [plot["file"] for plot in self.plots]:  # check if data is from a new routine
                                report_status(obj_response, "status", "Receiving data from '%s'." % obj.file)
                                yield from obj.create_routine(obj_response)
                            yield from obj.create(obj_response)
                            self.plots.append(dict(id=obj.id, file=obj.routine_list_id))
                        else:
                            yield from obj.update(obj_response)


class Handlers(object):
    """
    A base class for all SijaxHandlers classes.

    Args:
        app: The flask app.

    Attributes:
        app: The flask app.
    """
    def __init__(self, app):
        self.app = app


class SijaxUploadHandlers(Handlers):
    """
    Handlers object encapsulating Sijax upload Handlers.

    Encapsulation allows all handlers to be registered simultaneously.
    """
    def add_routine(self, obj_response, files, form_values):
        """
        Add a routine.

        Args:
            obj_response: Sijax object response.
            files: A list containing the Werkzeug FileStorage object for the uploaded file.
            form_values: Dictionary of form values. A required argument for Sijax upload handlers.
        """
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
        elif filename in (routine.name for routine in Routine.query.all()):
            report_status(obj_response, "status", "A routine with the name '%s' already exists." % filename)
        else:
            routine = Routine(self.app.config["UPLOAD_FOLDER"], filename)
            db.session.add(routine)
            db.session.commit()
            file_data.save(os.path.join(self.app.config["UPLOAD_FOLDER"], filename))
            obj_response.html_append("#routine-list", "<li class='routine' id='%s'>%s</li>" % (routine.file_id, filename))
            report_status(obj_response, "status", "Upload of '%s' successful." % filename)
        obj_response.attr("#routine-upload", "value", "")


class SijaxHandlers(Handlers):
    """
    Handlers object encapsulating regular Sijax handlers.
    """
    def stop_analysis(self, obj_response):
        """
        Stop the analysis.

        Args:
            obj_response: Sijax object response.
        """
        global analysis_on
        analysis_on = False
        report_status(obj_response, "status", "Analysis stopped")
        obj_response.call("reset_timer")

    def pause_analysis(self, obj_response):
        """
        Pause the analysis.

        Args:
            obj_response: Sijax object response.
        """
        global analysis_on
        analysis_on = False
        report_status(obj_response, "status", "Analysis paused")
        obj_response.call("stop_timer")

    def remove_routine(self, obj_response, file_ids):
        """
        Remove routines.

        Args:
            obj_response: Sijax object response.
            file_ids (list): The ids associated with the routines to remove.
        """
        filenames = []
        for file_id in file_ids:
            routine = get_objects(Routine, file_id=file_id)[0]
            filename = routine.name
            filenames.append(filename)
            try:
                os.remove(os.path.join(self.app.config["UPLOAD_FOLDER"], filename))
            except FileNotFoundError:
                report_status(obj_response, "status", "Unable to locate '%s'." % filename)
            db.session.delete(routine)
        if len(file_ids) > 3:
            report_status(obj_response, "status", "%s routines removed." % len(file_ids))
        else:
            report_status(obj_response, "status", "'%s' removed." % "', '".join(filenames))
        db.session.commit()

    def stop_routine(self, obj_response, file_ids):
        """
        Terminate routines.

        Args:
            obj_response: Sijax object response.
            file_ids (list): The ids associated with the routines to terminate.
        """
        for file_id in file_ids:
            routine = get_objects(Routine, file_id=file_id)[0]
            if routine.running:
                routine.stop(obj_response)
        db.session.commit()

    def pause_routine(self, obj_response, file_ids):
        """
        Pause routines.

        Args:
            obj_response: Sijax object response.
            file_ids: The ids associated with the routines to pause.
        """
        for file_id in file_ids:
            routine = get_objects(Routine, file_id=file_id)[0]
            if routine.running:
                routine.pause(obj_response)

    def run_routine(self, obj_response, file_id, routine_paused):
        """
        Run a routine.

        Unlike other routine handlers, this handler only acts on one routine at a time
        to take advantage of flask's built-in threading.

        Args:
            obj_response: Sijax object response.
            file_id (str): The id associated with the routine to run.
            routine_paused (bool): Whether the routine is in the paused state.
        """
        routine = get_objects(Routine, file_id=file_id)[0]
        if routine_paused:
            routine.resume(obj_response)
        else:
            p = routine.start()
            db.session.commit()
            p.wait()
            if routine.running:
                stdout, stderr = p.communicate()
                routine.running = False
                routine.report(obj_response, stdout)
            db.session.commit()

    def set_log(self, obj_response, log_path):
        """
        Set the log file path.

        Args:
            obj_response: Sijax object response.
            log_path (str): The new log path.
        """
        if not log_path:
            get_objects(Misc)[0].log_path = None
            db.session.commit()
            obj_response.html("#log-path", "None")
            report_status(obj_response, "status", "Logging stopped.")
        elif log_path and not os.path.isdir(os.path.split(log_path)[0]):
            report_status(obj_response, "status", "'%s' is not a valid directory." % os.path.split(log_path)[0])
        elif get_objects(Misc)[0].log_path != log_path:
            get_objects(Misc)[0].log_path = log_path
            db.session.commit()
            obj_response.html("#log-path", html.escape(log_path))
            report_status(obj_response, "status", "Log path changed to '%s'." % log_path)

class SijaxCometHandlers(Handlers):
    """
    Handlers object encapsulating Sijax comet handlers.

    Encapsulation allows all handlers to be registered simultaneously.
    """
    def analyse(self, obj_response, paused, period, current_plots):
        """
        Start the analysis.

        Args:
            obj_response: Sijax object response.
            paused (bool): Whether the analysis is in the paused state.
            period (float): The analysis period.
            current_plots (list): A list of dictionaries corresponding to currently active plots.
                Each dictionary contains the ids associated with the plot and its file.

        Yields:
            The updated Sijax object response.
        """
        analysis = Analysis(self.app, paused, period, current_plots)
        yield from analysis.start(obj_response)
        while analysis_on:
            yield from analysis.step(obj_response)
