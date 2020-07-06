
# import libraries
import sys
import getopt
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import inspect
import os
import contextlib


# context manager to prevent standard output
@contextlib.contextmanager
def no_stdout():
    save_stdout = sys.stdout
    sys.stdout = BytesIO()
    yield
    sys.stdout = save_stdout


# parse the options and arguments into a dictionary with data from previous measurements and the paths to the current measurement files
def parse_options():
    if sys.argv:
        options = sys.argv[1:]
        opts = getopt.getopt(options, "d:")
        data = None
        # check if -d option exists
        if len(opts[0]) > 0:
            data_path = opts[0][0][1]
            with open(data_path, "r") as file:
                data = json.load(file)
        paths = opts[1]
        return data, paths
    else:
        return None, None


# write data to the designated read-write file
def write_data(data):
    if sys.argv:
        options = sys.argv[1:]
        opts = getopt.getopt(options, "d:")
        # check if -d option exists
        if len(opts[0]) > 0:
            data_path = opts[0][0][1]
            with open(data_path, "w") as file:
                json.dump(data, file)


# decorator for plot functions
def plot(func):
    def plot_wrapper(*args, **kwargs):
        plot_wrapper.counter += 1
        # clear plot
        plt.clf()
        with no_stdout():
            # run plot function
            data = func(*args, **kwargs)
        # annotate plot with routine name and function name
        frame = inspect.stack()[1]
        filename = os.path.basename(frame[0].f_code.co_filename)
        plt.annotate("%s (%s)" % (filename, func.__name__), xy=(0, 0), xycoords='figure fraction')
        # if function output is dictionary, encode it as a json string
        if type(data) != dict:
            data = '{}'
        else:
            data = json.dumps(data)
        # encode plot in base64
        img = BytesIO()
        plt.savefig(img)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        # write information to standard output
        sys.stdout.write("@@@%s@@@%s@@@%s@@@%s" % (func.__name__, plot_wrapper.counter, plot_url, data))
    # set plot_wrapper attribute to display function information in GUI
    plot_wrapper.plot = True
    plot_wrapper.counter = 0
    plot_wrapper.__doc__ = func.__doc__
    return plot_wrapper
