
# import libraries
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import inspect
import os
import numpy as np
from time import time
import sys


# set global variables
app_root_path = ""


def add_support_paths(*args):
    for arg in args:
        sys.path.append(arg)


class Series(object):

    def __init__(self, name, time):
        self.name = name
        self.time = time
        self.data = []
        self.times = []
        self.start_time = self.now

    def get(self, *args):
        self.data += args
        if self.time:
            self.times += [self.start_time - self.now] * len(args)
            return self.times, self.data
        return self.data

    def time_series_plot(self, pnts=10, *args, **kwargs):
        plt.plot(self.times, self.data, *args, **kwargs)
        plt.xlim(max(0, self.num - pnts), self.num + pnts)

    @property
    def now(self):
        return time()

    @property
    def num(self):
        return len(self.data)


class Analysis(object):

    def __init__(self, interactive=False, save=False, save_path=None):
        self.data = []
        self.interactive = interactive
        if interactive:
            self.filename = "interactive"
        else:
            frame = inspect.stack()[1]
            self.filename = os.path.basename(frame[0].f_code.co_filename)
        self.data_path = os.path.join(self.get_app_root_path(), "plot_data", os.path.splitext(self.filename)[0])
        self.save = save
        if save:
            if save_path:
                self.save_path = save_path
            else:
                print("Warning: Save path not defined. Using current working directory.")
                self.save_path = os.getcwd()
        self.series = {}

    def get_app_root_path(self):
        """
        Get the app root path

        Returns:
            OSError: If app root path has not been configured
                or the configured app root path doesn't exist
                or the configured app root path does not contain a 'plot_data' directory.
        """
        global app_root_path
        if not app_root_path:
            msg = "App root path not configured. Try 'seneca_analysis.app_root_path = APP_ROOT_PATH'"
            self.message(msg)
            raise OSError(msg)
        elif not os.path.exists(app_root_path):
            msg = "App root path '%s' is not a valid path." % app_root_path
            self.message(msg)
            raise OSError(msg)
        elif "plot_data" not in os.listdir(app_root_path):
            msg = "App root path '%s' does not contain 'plot_data' directory. Check that the app root path has been configured properly." % app_root_path
            self.message(msg)
            raise OSError(msg)
        else:
            return app_root_path

    def send(self):
        """Send data to the analysis app."""
        np.save(self.data_path, self.data, allow_pickle=True)
        self.data = []

    def message(self, msg):
        """
        Send a message to the analysis app.

        The function stores the following information as a dictionary.
            1. The type of object, in this case "message".
            2. The name of the file where the Analysis object is initialized.
            3. The message argument.

        Args:
            msg: The message to send.
        """
        self.data.append(dict(type="message", file=self.filename, message=msg))

    def end(self):
        """Stop the analysis"""
        self.data.append(dict(type="complete", file=self.filename))
        self.send()

    def image(self, name, path, description=""):
        """
        Send an image to the analysis app.

        The function stores the following information as a dictionary.
            1. The type of object, in this case "image".
            2. The name of the file where the Analysis object is initialized.
            3. The name argument.
            4. The description argument, if provided.
            5. The base64 encoded string for the image.

        Args:
            name (str): A name to associate with the image in the analysis app.
            path (str): The path to the image file.
            description (str): A description of the image.

        Returns:
            FileNotFoundError: If the path argument is not a valid file path.
        """
        if os.path.isfile(path):
            # encode the image as a base64 string
            with open(path, "rb") as image_file:
                url = base64.b64encode(image_file.read()).decode()
            self.data.append(dict(type="image", file=self.filename, name=name, description=description, url=url))
        else:
            msg = "'%s' is not a valid file path"
            self.message(msg)
            self.end()
            raise FileNotFoundError(msg)

    def table(self, name, data, description=""):
        """
        Send a table to the analysis app.

        The function stores the following information as a dictionary.
            1. The type of object, in this case "table".
            2. The name of the file where the Analysis object is initialized.
            3. The name argument.
            4. The description argument, if provided.
            5. The data argument encoded as a json string.

        Args:
            name (str): A name to associate with the table in the analysis app.
            data (dict): The data to send to the analysis app.
            description (str): A description of the table.

        Return:
            ValueError: If the data argument is not a dictionary.
        """
        if type(data) == dict:
            data = json.dumps(data)
            self.data.append(dict(type="table", file=self.filename, name=name, description=description, data=data))
        else:
            msg = "Data for table '%s' is not a dictionary." % name
            self.message(msg)
            self.end()
            raise ValueError(msg)

    def plot(self, name, description="", save_name=None, no_save=False):
        """
        Send the current matplotlib plot to the analysis app.

        The function stores the following information as a dictionary
            1. The type of object, in this case "plot".
            2. The name of the file where the function is called.
            3. The name argument.
            4. The description argument, if provided.
            5. The base64 encoded string for the current matplotlib plot.

        Args:
            name (str): A name to associate with the plot in the analysis app.
            description (str): A description of the plot.
        """
        if self.save and not no_save:
            if not save_name:
                save_name = "%s-%s.png" % (name, time())
            full_save_path = os.path.join(self.save_path, save_name)
            plt.savefig(full_save_path)
        plt.annotate("%s (%s)" % (name, self.filename), xy=(0, 0), xycoords='figure fraction')  # annotate plot with file name and plot name
        # encode the plot as a base64 string
        img = BytesIO()
        plt.savefig(img)
        img.seek(0)
        url = base64.b64encode(img.getvalue()).decode()
        self.data.append(dict(type="plot", file=self.filename, name=name, description=description, url=url))
        plt.clf()

    def init_series(self, name, time=False):
        ser = Series(name, time)
        self.series[name] = ser
        return ser
