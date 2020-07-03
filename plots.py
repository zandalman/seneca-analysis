
# import libraries
import os
import subprocess
import json
import time


# get the paths of the measurement files to analyse based on the analysis options
def get_shots_paths(analysis_options, shots_dir, data_dir):
    # get measurement selection method
    select_method = analysis_options["select-shots-by"]
    # get the paths to all measurement files in the directory
    all_shots = [os.path.join(data_dir, shots_dir, shot) for shot in os.listdir(os.path.join(data_dir, shots_dir)) if os.path.isfile(os.path.join(data_dir, shots_dir, shot)) and not shot.startswith(".")]
    num_shots = int(analysis_options["num-shots"])
    filetypes = analysis_options["filetype"]
    now = time.time()
    period = 1 / get_period(analysis_options)
    if select_method == "choice":
        shots = [os.path.join(data_dir, shots_dir, shot) for shot in analysis_options["choice"]]
    elif select_method == "all":
        shots = all_shots
    elif select_method == "last-created":
        all_shots.sort(key=os.path.getctime)
        shots = all_shots[-num_shots:]
    elif select_method == "last-modified":
        all_shots.sort(key=os.path.getmtime)
        shots = all_shots[-num_shots:]
    elif select_method == "new":
        shots = [shot for shot in all_shots if now - os.path.getctime(shot) <= period]
    elif select_method == "modified":
        shots = [shot for shot in all_shots if now - os.path.getmtime(shot) <= period]
    if filetypes:
        all_filetypes = []
        for filetype in filetypes:
            all_filetypes += filetype.split("/")
        shots = [shot for shot in shots if shot.rsplit('.', 1)[1].lower() in all_filetypes]
    return shots

def get_all_shots_paths_old(analysis_options, shots_dir, data_dir):
    order_method = analysis_options["order-shots-by"]
    all_shots = [os.path.join(data_dir, shots_dir, shot) for shot in os.listdir(os.path.join(data_dir, shots_dir)) if os.path.isfile(os.path.join(data_dir, shots_dir, shot)) and not shot.startswith(".")]
    filetypes = analysis_options["filetype"]
    if order_method == "choice":
        shots = [os.path.join(data_dir, shots_dir, shot) for shot in analysis_options["choice"]]
    elif order_method == "creation":
        all_shots.sort(key=os.path.getctime)
        shots = all_shots
    elif order_method == "modification":
        all_shots.sort(key=os.path.getmtime)
        shots = all_shots
    if filetypes:
        all_filetypes = []
        for filetype in filetypes:
            all_filetypes += filetype.split("/")
        shots = [shot for shot in shots if shot.rsplit('.', 1)[1].lower() in all_filetypes]
    return shots


# run the routines and generate the plot urls
def generate_plot_urls(routine, routine_path, data_dir, shots_paths=None):
    if not shots_paths:
        shots_paths = get_shots_paths(routine["analysis"]["new_options"], routine["shots_dir"], data_dir)
    path_to_routine = os.path.join(routine_path, routine["name"])
    # create a list of arguments to pass to the command line
    arguments = ["python", path_to_routine]
    if routine["json"]:
        arguments += ["-d", os.path.join(data_dir, routine["json"])]
    arguments += shots_paths
    try:
        # run the routine
        out = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except Exception as err:
        return True, err
    # get the standard output
    stdout, stderr = out.communicate()
    try:
        # parse the standard output
        function_name_list = str(stdout)[:-1].split("SEPARATOR")[1:][::3]
        plot_url_list = str(stdout)[:-1].split("SEPARATOR")[1:][1::3]
        plot_data_list = str(stdout)[:-1].split("SEPARATOR")[1:][2::3]
        # generate a list of dictories with information about the plots
        plots = []
        for i in range(len(function_name_list)):
            plot_id = "plot-container-%s" % function_name_list[i]
            plot_url = "data:image/png;base64,{}".format(plot_url_list[i])
            plot_data = json.loads(plot_data_list[i])
            table_id = "table-container-%s" % function_name_list[i]
            plots.append(dict(plot_id=plot_id, url=plot_url, data=plot_data, table_id=table_id))
    except IndexError:
        return True, "".join(str(stdout)[2:-1].split("\\n"))
    return False, plots


# create and initialize a plot and associated data table
def create_plot(obj_response, plot_id, table_id, plot_data, plot_url, routine_name, plot_list_HTML):
    function_name = plot_id[15:]
    obj_response.html_append("#plots-container", "<div id='%s' class='plot-container' title='%s (%s)' style='display: none;'></div>" % (plot_id, routine_name, function_name))
    plot_list_HTML += "<li class='plot-list-item invisible' data-id='%s'>%s</li>" % (plot_id, function_name)
    obj_response.call("init_img", [plot_url, plot_id])
    if plot_data:
        caption = "<caption>%s (%s)</caption>" % (routine_name, function_name)
        plot_table_body = ""
        for param in sorted(plot_data.keys()):
            plot_table_body += "<tr><th>%s</th><td>%s</td></tr>" % (param, plot_data[param])
        plot_table = "<div class='table-container' id='%s' title='%s (%s)' style='display: none;'><table>%s<tbody>%s</tbody></table></div>" % (table_id, routine_name, function_name, caption, plot_table_body)
        obj_response.html_append("#plots-container", plot_table)
        plot_list_HTML += "<li class='plot-list-item invisible' data-id='%s'>%s - table</li>" % (table_id, function_name)
        obj_response.call("init_table", [table_id])
    return plot_list_HTML


# update a plot and associated data table
def update_plot(obj_response, url, plot_id, plot_data, table_id, routine_name):
    obj_response.call("update_img", [url, plot_id, "true"])
    if plot_data:
        function_name = plot_id[15:]
        caption = "<caption>%s (%s)</caption>" % (routine_name, function_name)
        plot_table_body = ""
        for param in sorted(plot_data.keys()):
            plot_table_body += "<tr><th>%s</th><td>%s</td></tr>" % (param, plot_data[param])
        plot_table = "<table>%s<tbody>%s</tbody></table>" % (caption, plot_table_body)
        obj_response.html("#%s" % table_id, plot_table)


# remove all plots and data tables
def remove_plots(obj_response):
    obj_response.html("#plots-container, #plot-list", "")


# initialize all plots and data tables for a routine
def initialize_routine(obj_response, routine_path, routine, data_dir, initial_shots):
    if initial_shots:
        error, plots = generate_plot_urls(routine, routine_path, data_dir, shots_paths=initial_shots)
    else:
        error, plots = generate_plot_urls(routine, routine_path, data_dir)
    if error:
        return True, plots
    routine_name = routine["name"]
    plot_ids = []
    plot_list_HTML = "<ul class='plot-list-routine' id='plot-list-%s'>" % routine_name
    plot_list_HTML += "<li class='plot-list-routine-title invisible'><b>%s</b></li>" % routine_name
    for plot in plots:
        plot_ids.append(plot["plot_id"])
        plot_list_HTML = create_plot(obj_response, plot["plot_id"], plot["table_id"], plot["data"], plot["url"], routine_name, plot_list_HTML)
    plot_list_HTML += "</ul>"
    obj_response.html_append("#plot-list", plot_list_HTML)
    return False, plot_ids


# check if a routine has enough settings to be used in analysis
def is_routine_active(routine):
    if routine["shots_dir"] == "":
        return False
    return True


# get the period of the analysis
def get_period(analysis_options):
    frequency = analysis_options["frequency"]
    if float(frequency) == 0:
        # set period to 1000 s to avoid divide by zero error
        period = 1000
    else:
        period = 1 / float(frequency)
    return period