
# import libraries
import sys
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import inspect
import os
import contextlib
import importlib

PATH_TO_PLOT_DATA = "./plot_data"

# context manager to prevent standard output
@contextlib.contextmanager
def no_stdout():
    save_stdout = sys.stdout
    sys.stdout = BytesIO()
    yield
    sys.stdout = save_stdout


def reset_plot_counters():
    frame = inspect.stack()[1]
    filename = os.path.basename(frame[0].f_code.co_filename)
    routine_mod = importlib.import_module(inspect.getmodulename(filename))
    plot_functions = [getattr(routine_mod, func[0]) for func in inspect.getmembers(routine_mod, predicate=inspect.isfunction) if not func[0].startswith("_") and hasattr(getattr(routine_mod, func[0]), "plot")]
    for plot_function in plot_functions:
        plot_function.counter = 0


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
            data = "{}"
        else:
            data = json.dumps(data)
        # encode plot in base64
        img = BytesIO()
        plt.savefig(img)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        # write information to standard output
        output_info = "@@@%s@@@%s@@@%s@@@%s" % (func.__name__, plot_wrapper.counter, plot_url, data)
        with open(PATH_TO_PLOT_DATA, 'w') as plot_data:
            plot_data.write(output_info)
        # set plot_wrapper attribute to display function information in GUI
        plot_wrapper.plot = True
        plot_wrapper.counter = 0
        plot_wrapper.__doc__ = func.__doc__
        return plot_wrapper
    return plot