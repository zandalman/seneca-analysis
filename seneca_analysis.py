
# import libraries
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import inspect
import os
import importlib

PLOT_DATA_PATH = "/Users/zacharyandalman/PycharmProjects/analysis/plot_data/plot_data"

def plot(interactive=False, multiple=False):
    def plot_decorator(func):
        def plot_wrapper(*args, **kwargs):
            if multiple:
                reset = kwargs.pop("reset", False)
                if not reset:
                    # increment plot counter
                    plot_wrapper.counter += 1
            # close any open plots
            plt.close()
            data = func(*args, **kwargs)
            # annotate plot with routine name and function name
            if interactive:
                filename = "interactive"
            else:
                frame = inspect.stack()[1]
                filename = os.path.basename(frame[0].f_code.co_filename)
            plt.annotate("%s (%s)" % (filename, func.__name__), xy=(0, 0), xycoords='figure fraction')
            # if function output is dictionary, encode it as a json string
            if type(data) != dict:
                data = "{}"
            else:
                data = json.dumps(data)
            # encode the plot in base64
            img = BytesIO()
            plt.savefig(img)
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()
            # write information to standard output
            output_info = "@@@" + "@@@".join([str(info) for info in [filename, func.__name__, func.__doc__, plot_wrapper.counter, plot_url, data]])
            with open(PLOT_DATA_PATH, 'w') as plot_data:
                plot_data.write(output_info)
        plot_wrapper.plot = True
        # initialize plot counter
        plot_wrapper.counter = 0
        plot_wrapper.__doc__ = func.__doc__
        return plot_wrapper
    return plot_decorator
