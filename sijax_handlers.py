
import numpy as np
import time
from werkzeug import secure_filename
from plots import *
from models import *

# do one analysis iteration
def analysis_step(app, obj_response):
    for plot_data_file in os.listdir(app.config["PLOT_DATA_FOLDER"]):
        plot_data_file_path = os.path.join(app.config["PLOT_DATA_FOLDER"], plot_data_file)
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
                    os.remove(os.path.join(app.config["PLOT_DATA_FOLDER"], "%s.npy" % os.path.splitext(plot_data["file"])[0]))
                    yield obj_response
                else:
                    obj = obj_types[plot_data["type"]](plot_data)
                    if obj.id not in [plot["id"] for plot in Misc.query.first().current_plots]:
                        if not obj.file in [plot["file"] for plot in Misc.query.first().current_plots]: # check if data is from a new routine
                            report_status(obj_response, "status", "Receiving data from '%s'." % obj.file)
                            yield from obj.create_routine(obj_response)
                        yield from obj.create(obj_response)
                        Misc.query.first().current_plots.append(dict(file=obj.file, id=obj.id))
                        db.session.commit()
                    else:
                        yield from obj.update(obj_response)

class Handlers(object):

    def __init__(self, app):
        self.app = app

class SijaxUploadHandlers(Handlers):

    def add_routine(self, obj_response, files, form_values):
        print("test")
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
            print("test")
            routine = Routine(self.app.config["UPLOAD_FOLDER"], filename)
            db.session.add(routine)
            db.session.commit()
            file_data.save(os.path.join(self.app.config["UPLOAD_FOLDER"], filename))
            obj_response.html_append("#routine-list", "<li class='routine' id='%s'>%s</li>" % (routine.file_id, filename))
            report_status(obj_response, "status", "Upload of '%s' successful." % filename)


class SijaxHandlers(Handlers):

    def stop_analysis(self, obj_response):
        """Stop the analysis."""
        Misc.query.first().analysis_on = False
        db.session.commit()
        report_status(obj_response, "status", "Analysis stopped")
        obj_response.call("reset_timer")

    def pause_analysis(self, obj_response):
        """Pause the analysis."""
        Misc.query.first().analysis_on = False
        db.session.commit()
        report_status(obj_response, "status", "Analysis paused")
        obj_response.call("stop_timer")

    def remove_routine(self, obj_response, file_ids):
        filenames = []
        for file_id in file_ids:
            routine = get_routines(file_id=file_id)
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
        for file_id in file_ids:
            routine = get_routines(file_id=file_id)
            if routine.running:
                routine.stop(obj_response)
        db.session.commit()

    def run_routine(self, obj_response, file_id):
        routine = get_routines(file_id=file_id)
        p = routine.start()
        db.session.commit()
        p.wait()
        if routine.running:
            stdout, stderr = p.communicate()
            routine.running = False
            routine.report(obj_response, stdout)
        db.session.commit()

class SijaxCometHandlers(Handlers):

    def analyse(self, obj_response, paused, period):
        """Start the analysis."""
        Misc.query.first().analysis_on = True
        db.session.commit()
        if paused:
            report_status(obj_response, "status", "Analysis restarted")
        else:
            report_status(obj_response, "status", "Analysis started")
            remove_plots(obj_response)
            Misc.query.first().current_plots = []
            db.session.commit()
            for plot_data_file in os.listdir(self.app.config["PLOT_DATA_FOLDER"]):
                os.remove(os.path.join(self.app.config["PLOT_DATA_FOLDER"], plot_data_file))
        obj_response.call("start_timer") # start the timer
        yield obj_response
        give_warning = True
        while Misc.query.first().analysis_on:
            step_start_time = time.time()
            yield from analysis_step(self.app, obj_response)
            step_time = time.time() - step_start_time
            if period > step_time:
                time.sleep(period - step_time)
            else:
                if give_warning: # Check if warning has already been given for this routine
                    report_status(obj_response, "status", "Warning: Period is shorter than execution time by %.3g seconds" % (step_time - period))
                    give_warning = False