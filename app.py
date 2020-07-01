
# import modules
from flask import Flask, render_template, g
import os, sys
import flask_sijax
from werkzeug import secure_filename
import json
import inspect
import importlib
import time
from plots import *
# initialize and configure Flask
app = Flask(__name__)
sijax_path = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')
app.config.update(
    SIJAX_STATIC_PATH=sijax_path,
    SIJAX_JSON_URI='/static/js/sijax/json2.js'
)
flask_sijax.Sijax(app)
# add routines to path
routine_path = os.path.join(app.root_path, "routines")
JSON_path = os.path.join(routine_path, "routines.json")
sys.path.append(routine_path)
# set global variables
analysis_on = False


# read a python script and write information to json
def get_routine_info(routine_name):
    routine_info = {}
    # try to import the routine as a module
    try:
        routine_mod = importlib.import_module(inspect.getmodulename(routine_name))
    except Exception as err:
        routine_info["error"] = "'%s' does not compile: '%s: %s'" % (routine_name, err.__class__.__name__, err)
        return routine_info
    # add description from docstring
    if routine_mod.__doc__:
        routine_info["description"] = str(routine_mod.__doc__)
    # get plot functions
    function_names = [func[0] for func in inspect.getmembers(routine_mod, predicate=inspect.isfunction) if not func[0].startswith("_") and hasattr(getattr(routine_mod, func[0]), "plot")]
    if len(function_names) == 0:
        routine_info["error"] = "'%s' has no plot functions" % routine_name
    routine_info["functions"] = []
    # get descriptions of plot functions from docstrings
    for function_name in function_names:
        function = getattr(routine_mod, function_name)
        routine_info["functions"].append(dict(name=function_name, description=function.__doc__))
    return routine_info


# a wrapper for the recursive make_tree function
def make_tree_wrapper():
    global routine_path, JSON_path
    # read paths and routines from the routine json file
    with open(JSON_path, 'r') as file:
        data = json.load(file)
        paths = list(map(lambda path: path.split('/'), data["paths"]))
        routines = [routine for routine in data["routines"] if routine["name"] in os.listdir(routine_path)]
        supports = [support for support in data["support"] if support["name"] in os.listdir(routine_path)]

    # create a nested file/folder object from json file to pass to the main template
    def make_tree(tree_path):
        if tree_path:
            name = tree_path[-1]
        else:
            name = ""
        tree_path_joined = "/".join(tree_path)
        tree = dict(name=name, children=[], path=tree_path_joined)
        subpaths = [path for path in paths if len(path) == len(tree_path) + 1 and path[:-1] == tree_path]
        for subpath in subpaths:
            tree["children"].append(make_tree(subpath))
        subroutines = [routine for routine in routines if routine["path"] == tree_path_joined]
        for subroutine in subroutines:
            tree["children"].append(dict(name=subroutine["name"], path=subroutine["path"], routine=True))
        subsupports = [support for support in supports if support["path"] == tree_path_joined]
        for subsupport in subsupports:
            tree["children"].append(dict(name=subsupport["name"], path=subsupport["path"], routine=False))
        return tree
    return make_tree([])


# decorator generator for reading and writing to the routine json file
def update_JSON(write = True):
    global JSON_path

    # decorator for reading and writing to the routine json file
    def decorator(func):

        def wrapper(*args, **kwargs):
            # read the routine json file
            with open(JSON_path, "r") as file:
                data = json.load(file)
            data = func(*args, **kwargs, data=data)
            if write:
                # write to the routine json file
                with open(JSON_path, "w") as file:
                    json.dump(data, file)
        return wrapper
    return decorator


# send a message to an html element
def report_status(obj_response, container_id, msg):
    obj_response.html_append("#%s" % container_id, "%s<br/>" % msg)


# get the data directory from the routine json file
def get_data_dir():
    global JSON_path
    with open(JSON_path, "r") as file:
        data_dir = json.load(file)["data_dir"]
    if data_dir == "":
        return "None"
    else:
        return data_dir


# count the files in the shots directory separated by file type
def count_files(dir):
    file_count = {"total": 0}
    filenames = [filename for filename in os.listdir(dir) if os.path.isfile(os.path.join(dir, filename)) and not filename.startswith(".")]
    for filename in filenames:
        extension = filename.rsplit('.', 1)[1].lower()
        if extension in file_count.keys():
            file_count[extension] += 1
        else:
            file_count[extension] = 1
        file_count["total"] += 1
    return file_count


# update the shots count table
def update_shots_count(obj_response, shots_dir_path):
    obj_response.html("#shots-table-body", "")
    file_count = count_files(shots_dir_path)
    for filetype in file_count.keys():
        if filetype != "total":
            obj_response.html_append("#shots-table-body", "<tr><td>%s</td><td>%d</td></tr>" % (filetype, file_count[filetype]))
    # display the total number of files if there are multiple file types
    if len(file_count.keys()) != 2:
        obj_response.html_append("#shots-table-body", "<tr><td>%s</td><td>%d</td></tr>" % ("total", file_count["total"]))


# update the options for the shots directory
def update_shots_dir_options(obj_response, routine, data_dir):
    # if there's no data directory, hide all shots information
    if data_dir == "":
        obj_response.css('.shots-info', "display", "none")
        return
    elif not os.path.isdir(data_dir):
        report_status(obj_response, "status", "Warning: '%s' is no longer a valid directory" % data_dir)
        return
    obj_response.css('.shots-info', "display", "inline")
    # list all subdirectories of the data directory
    subdirs = [subdir for subdir in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, subdir))]
    # add the 'none' option
    obj_response.html("#shots-dir-options", "<option value=''>none</option>")
    shots_dir = routine["shots_dir"]
    # add an option for each subdirectory and select the option if necessary
    for subdir in subdirs:
        if shots_dir == subdir:
            obj_response.html_append("#shots-dir-options", "<option value='%s' selected>%s</option>" % (subdir, subdir))
        else:
            obj_response.html_append("#shots-dir-options", "<option value='%s'>%s</option>" % (subdir, subdir))
    # if there's no shots directory, hide the shots table
    if shots_dir == "":
        obj_response.css("#shots-table", "display", "none")
    else:
        obj_response.css("#shots-table", "display", "inline")
        shots_dir_path = os.path.join(data_dir, shots_dir)
        update_shots_count(obj_response, shots_dir_path)
        update_shots_choice(obj_response, routine, data_dir)


# check if a file is json loadable
def is_json_loadable(filename):
    try:
        json.load(open(filename))
        return True
    except Exception:
        return False


# update the read-write json file options
def update_json_options(obj_response, routine, data_dir):
    # if there's no data directory, hide all shots information
    if data_dir == "":
        obj_response.css('.shots-info', "display", "none")
        return
    elif not os.path.isdir(data_dir):
        report_status(obj_response, "status", "Warning: '%s' is no longer a valid directory" % data_dir)
        return
    obj_response.css('.shots-info', "display", "inline")
    # list all json loadable files in the data directory
    json_options = [file for file in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, file)) and is_json_loadable(os.path.join(data_dir, file))]
    obj_response.html("#json-options", "<option value=''>none</option>")
    # add an option for each json file and select the option if necessary
    for json_file in json_options:
        if json_file == routine["json"]:
            obj_response.html_append("#json-options", "<option value='%s' selected>%s</option>" % (json_file, json_file))
        else:
            obj_response.html_append("#json-options", "<option value='%s'>%s</option>" % (json_file, json_file))


# update the shots choice options
def update_shots_choice(obj_response, routine, data_dir):
    choice = routine["analysis"]["choice"]
    shots_dir_path = os.path.join(data_dir, routine["shots_dir"])
    # list all files in the shots directory
    shots = [shot for shot in os.listdir(shots_dir_path) if os.path.isfile(os.path.join(shots_dir_path, shot)) and not shot.startswith(".")]
    # reset the shots choice options
    obj_response.html("#shots-choice", "")
    # add an option for each file and select the option if necessary
    for shot in shots:
        obj_response.html_append("#shots-choice", "<option value='%s'>%s</option>" % (shot, shot))
        if shot in choice:
            obj_response.attr("option[value|='%s']" % shot, "selected", "selected")

def update_filetype(obj_response, routine):
    filetypes = routine["analysis"]["filetype"]
    obj_response.call("select_filetype", [filetypes])

# update the analysis options
def update_analysis_options(obj_response, routine, data_dir):
    analysis_method = routine["analysis"]["select-shots-by"]
    num_shots = routine["analysis"]["num-shots"]
    frequency = routine["analysis"]["frequency"]
    obj_response.attr("option[value|='%s']" % analysis_method, "selected", "selected")
    obj_response.attr("#num-shots", "value", num_shots)
    obj_response.attr("#frequency", "value", frequency)
    update_shots_choice(obj_response, routine, data_dir)
    update_filetype(obj_response, routine)
    obj_response.call("check_shots_display")


# update the routine functions table
def update_functions(obj_response, routine):
    obj_response.css('#function-table', "display", "inline")
    obj_response.html('#function-table-body', "")
    for function in routine["functions"]:
        if function["description"]:
            description_string = function["description"]
        else:
            description_string = "None"
        obj_response.html_append("#function-table-body", "<tr><td class='func-name'>%s</td><td>%s</td></tr>" % (function["name"], description_string))


# check if file is a python script
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['py']


# add a routine
def add_routine(obj_response, files, form_values, data):
    global routine_path
    file_data = files['routine']
    filename = file_data.filename
    # send a warning if nothing is uploaded
    if filename is None:
        report_status(obj_response, "status", "Nothing uploaded")
        return data
    # send a warning if the file is not a python script
    elif not allowed_file(filename):
        report_status(obj_response, "status", "'%s' is not a python script" % filename)
        return data
    # send a warning if another routine exists with the same name
    elif filename in [routine["name"] for routine in data["routines"]]:
        report_status(obj_response, "status", "A routine by the name '%s' already exists" % filename)
        return data
    elif filename in [support["name"] for support in data["support"]]:
        report_status(obj_response, "status", "A supporting file by the name '%s' already exists" % filename)
        return data
    path = form_values['path'][0]
    file_path_app = os.path.join(routine_path, filename)
    file_data.save(file_path_app)
    routine_info = get_routine_info(filename)
    # check for errors from get_routine_info
    if "error" in routine_info.keys():
        report_status(obj_response, "status", routine_info["error"])
        os.remove(os.path.join(routine_path, filename))
        return data
    # set default analysis options
    default_analysis_options = {"select-shots-by": "choice", "num-shots": "1", "choice": [], "frequency": ".2", "filetype": []}
    routine_all_info = dict(name=filename, path=path, shots_dir="", json="", analysis=default_analysis_options)
    routine_all_info.update(routine_info)
    data['routines'].append(routine_all_info)
    obj_response.call('add_file', [path, filename, True])
    report_status(obj_response, "status", "'%s' successfully uploaded" % filename)
    return data

# add a supporting file
def add_support(obj_response, files, form_values, data):
    global routine_path
    file_data = files['support']
    filename = file_data.filename
    # send a warning if nothing is uploaded
    if filename is None:
        report_status(obj_response, "status", "Nothing uploaded")
        return data
    # send a warning if another routine exists with the same name
    elif filename in [routine["name"] for routine in data["routines"]]:
        report_status(obj_response, "status", "A routine by the name '%s' already exists" % filename)
        return data
    elif filename in [support["name"] for support in data["support"]]:
        report_status(obj_response, "status", "A supporting file by the name '%s' already exists" % filename)
        return data
    path = form_values['path'][0]
    file_path_app = os.path.join(routine_path, filename)
    file_data.save(file_path_app)
    data['support'].append(dict(name=filename, path=path))
    obj_response.call('add_file', [path, filename, False])
    report_status(obj_response, "status", "'%s' successfully uploaded" % filename)
    return data

# Sijax handlers for the main page
class MainHandler(object):
    # add a folder
    @staticmethod
    @update_JSON()
    def add_folder(obj_response, path, name, data={}):
        data['paths'].append(os.path.join(str(path), secure_filename(str(name))))
        return data

    # remove a routine
    @staticmethod
    @update_JSON()
    def remove_file(obj_response, filename, is_routine, data={}):
        global routine_path
        if is_routine:
            data['routines'] = [routine for routine in data["routines"] if routine['name'] != str(filename)]
        else:
            data['support'] = [support for support in data["support"] if support['name'] != str(filename)]
        os.remove(os.path.join(routine_path, filename))
        return data

    # remove a folder including all sub-folders and sub-routines
    @staticmethod
    @update_JSON()
    def remove_folder(obj_response, tree_path, data={}):
        global routine_path
        # remove all subpaths from paths
        tree_path_split = str(tree_path).split('/')
        paths = list(map(lambda path: path.split('/'), data["paths"]))
        data['paths'] = ["/".join(path) for path in paths if len(path) <= len(tree_path_split) or path[:len(tree_path_split)] != tree_path_split]
        # remove all subroutines
        routines_to_remove = [routine["name"] for routine in data["routines"] if len(routine['path'].split("/")) + 1 > len(tree_path_split) and (routine['path'].split('/') + [""])[:len(tree_path_split)] == tree_path_split]
        data['routines'] = [routine for routine in data["routines"] if len(routine['path'].split("/")) + 1 <= len(tree_path_split) or (routine['path'].split('/') + [""])[:len(tree_path_split)] != tree_path_split]
        for routine_name in routines_to_remove:
            os.remove(os.path.join(routine_path, routine_name))
        # remove folder
        data['paths'].remove(str(tree_path))
        return data


    # add a routine
    @staticmethod
    @update_JSON()
    def _add_file(obj_response, files, form_values, data={}):
        if 'routine' not in files:
            report_status(obj_response, "status", "Upload unsuccessful")
            return data
        if 'support' in files and files['support'].filename != '':
            data = add_support(obj_response, files, form_values, data)
            return data
        else:
            data = add_routine(obj_response, files, form_values, data)
            return data

    # select a data directory
    @staticmethod
    @update_JSON()
    def select_data_dir(obj_response, data_dir, update_dir_options, routine_name, data={}):
        if routine_name != "":
            routine = [routine for routine in data["routines"] if routine["name"] == routine_name][0]
        else:
            routine = dict(shots_dir="")
        # set the data directory to none
        if data_dir == "reset":
            data["data_dir"] = ""
            obj_response.html("#data-dir", "<b>data directory</b>: None")
            report_status(obj_response, "status", "Reset data directory")
            if update_dir_options:
                update_shots_dir_options(obj_response, routine, data["data_dir"])
                update_json_options(obj_response, routine, data["data_dir"])
                update_analysis_options(obj_response, routine, data["data_dir"])
            return data
        elif not os.path.isdir(data_dir):
            report_status(obj_response, "status", "'%s' is not a valid directory" % data_dir)
            return data
        elif not os.path.isabs(data_dir):
            report_status(obj_response, "status", "'%s' is not an absolute path" % data_dir)
            return data
        data["data_dir"] = data_dir
        for routine in data["routines"]:
            routine["shots-dir"] = ""
            routine["json"] = ""
        obj_response.html("#data-dir", "<b>data directory</b>: %s" % data_dir)
        report_status(obj_response, "status", "Changed data directory to '%s'" % data_dir)
        # update all displays based on new data directory
        if update_dir_options:
            update_shots_dir_options(obj_response, routine, data["data_dir"])
            update_json_options(obj_response, routine, data["data_dir"])
            update_analysis_options(obj_response, routine, data["data_dir"])
        return data

    # display routine information
    @staticmethod
    @update_JSON(write=False)
    def display_routine_info(obj_response, routine_name, data={}):
        routine = [routine for routine in data["routines"] if routine["name"] == routine_name][0]
        obj_response.html('#routine-name', "<b>routine name</b>: %s" % routine["name"])
        if "description" in routine.keys():
            obj_response.html('#routine-description', "<b>routine description</b>: %s" % routine["description"])
        # update all displays
        update_functions(obj_response, routine)
        update_shots_dir_options(obj_response, routine, data["data_dir"])
        update_json_options(obj_response, routine, data["data_dir"])
        update_analysis_options(obj_response, routine, data["data_dir"])

    # set shots directory for a routine
    @staticmethod
    @update_JSON()
    def set_shots_dir(obj_response, routine_name, shots_dir_form, data={}):
        routine = [routine for routine in data["routines"] if routine["name"] == routine_name][0]
        shots_dir = shots_dir_form["shots-dir-options"]
        routine["shots_dir"] = shots_dir
        if shots_dir == "":
            obj_response.css("#shots-table", "display", "none")
            report_status(obj_response, "status", "Removed shots directory for '%s'" % routine_name)
        else:
            report_status(obj_response, "status", "Shots directory for '%s' set to '%s'" % (routine_name, shots_dir))
            obj_response.css("#shots-table", "display", "inline")
            shots_dir_path = os.path.join(data["data_dir"], shots_dir)
            update_shots_count(obj_response, shots_dir_path)
            update_shots_choice(obj_response, routine, data["data_dir"])
        return data

    # set the options for the read-write json file
    @staticmethod
    @update_JSON()
    def set_json_options(obj_response, routine_name, json_file_form, data = {}):
        routine = [routine for routine in data["routines"] if routine["name"] == routine_name][0]
        json_file = json_file_form["json-options"]
        routine["json"] = json_file
        if json_file == "":
            report_status(obj_response, "status", "Removed JSON file for '%s'" % routine_name)
        else:
            report_status(obj_response, "status", "JSON file for '%s' set to '%s'" % (routine_name, json_file))
        return data

    # update analysis options
    @staticmethod
    @update_JSON()
    def update_analysis(obj_response, routine_name, analysis_options, shots_choice, filetypes, data={}):
        routine = [routine for routine in data["routines"] if routine["name"] == routine_name][0]
        analysis_options["choice"] = [shot["id"] for shot in shots_choice]
        analysis_options["filetype"] = [filetype["id"] for filetype in filetypes]
        routine["analysis"] = analysis_options
        report_status(obj_response, "status", "Set the analysis options for '%s' to '%s'" % (routine_name, analysis_options))
        return data

    # refresh analysis options
    @staticmethod
    @update_JSON(write=False)
    def refresh_analysis(obj_response, routine_name, data={}):
        routine = [routine for routine in data["routines"] if routine["name"] == routine_name][0]
        update_analysis_options(obj_response, routine, data["data_dir"])
        report_status(obj_response, "status", "Analysis options for '%s' reverted" % routine_name)

# Sijax handlers for the plot page
class PlotHandler(object):

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
    @update_JSON(write=False)
    def analyse(obj_response, paused, data={}):
        global routine_path
        data_dir = data["data_dir"]
        if not paused:
            remove_plots(obj_response)
        for routine in data["routines"]:
            if is_routine_active(routine):
                if not paused:
                    # initialize the plots and data tables
                    initialization_error, plot_ids = initialize_routine(obj_response, routine_path, routine, data_dir)
                    if initialization_error:
                        report_status(obj_response, "status", "Analysis failed: '%s: %s'" % (plot_ids.__class__.__name__, plot_ids))
                        obj_response.attr("#start-analysis", "class", "material-icons button")
                        obj_response.attr("#stop-analysis, #pause-analysis", "class", "material-icons button inactive")
                        return
                period = get_period(routine["analysis"])
                # make a request for analyse_routine
                obj_response.call("make_comet_request", [data_dir, routine, period])
        if paused:
            report_status(obj_response, "status", "Analysis restarted")
        else:
            report_status(obj_response, "status", "Analysis started")
        # start the timer
        obj_response.call("start_timer")


# Sijax comet handlers for the plot page
class PlotCometHandler(object):

    # periodically update the plot and data tables for a routine
    @staticmethod
    def analyse_routine(obj_response, data_dir, routine, period):
        global analysis_on, routine_path, JSON_path
        analysis_on = True
        reported_error = False
        # loop analysis until paused or stopped
        while analysis_on:
            iter_start = time.time()
            error, plots = generate_plot_urls(routine, routine_path, data_dir)
            if error:
                report_status(obj_response, "status", plots)
                PlotHandler.stop_analysis(obj_response)
            for plot in plots:
                update_plot(obj_response, plot["url"], plot["plot_id"], plot["data"], plot["table_id"], routine["name"])
                yield obj_response
            sleep_time = period - (time.time() - iter_start)
            if sleep_time >= 0:
                time.sleep(sleep_time)
            elif not reported_error:
                report_status(obj_response, "status", "Warning: update period is faster than execution time by %.3g seconds for '%s'. Try setting a lower frequency" % (-sleep_time, routine["name"]))
                reported_error = True

# route the main page
@flask_sijax.route(app, '/')
def main():

    data_dir = get_data_dir()
    # register Sijax upload handlers
    form_init_js = ''
    form_init_js += g.sijax.register_upload_callback('add-file', MainHandler._add_file)
    if g.sijax.is_sijax_request:
        # register Sijax handlers
        g.sijax.register_object(MainHandler)
        return g.sijax.process_request()
    routines = make_tree_wrapper()
    # render template
    return render_template('main.html', form_init_js=form_init_js, routines=routines, data_dir=data_dir)

# route the plot page
@flask_sijax.route(app, '/plot')
def main_plot():

    if g.sijax.is_sijax_request:
        # register Sijax handlers
        g.sijax.register_object(PlotHandler)
        # register Sijax comet handlers
        g.sijax.register_comet_object(PlotCometHandler)
        return g.sijax.process_request()
    # render template
    return render_template('plot.html')


# run the flask app with threads in debug mode
app.run(threaded=True, debug=True)