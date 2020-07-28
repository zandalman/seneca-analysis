
# import libraries
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import inspect
import os
import numpy as np
import time
import datetime
import sys
import errno


# set global variables
app_root_path = ""


def add_paths(*args):
    """
    Add paths available to Python.

    This function is required if the routine uses any local modules.

    Args:
        *args: Paths to add.
    """
    for arg in args:
        sys.path.append(arg)


class Series(object):
    """
    Series object for handling data series data.

    Args:
        name (str): A name to associate with the series.
        influx (bool): Connect the series to the InfluxDB database. Defaults to False.

    Attributes:
        name (str): A name to associate with the series.
        data (list): A list of series data.
        times (list): The time in seconds since initialization for each entry in data.
        start_time (float): The initialization time.
        pending (bool): Some data has not yet been sent.
        num (int): The number of entries in the series data.
        influx (bool): Connect the series to the InfluxDB database. Defaults to False.
    """
    def __init__(self, name, influx=False):
        self.name = name
        self.data = []
        self.times = []
        self.pending = False
        self.start_time = time.time()
        self.influx = influx

    def add(self, *args):
        """
        Add new entries the series.

        Args:
            *args: New entries to add.
        """
        self.data += args
        self.times += [time.time() - self.start_time] * len(args)
        self.pending = True

    def time_plot(self, width=20, *args, **kwargs):
        """
        Create a moving time series plot.

        Args:
            width: The range of the x-axis in seconds.
            *args: Arguments to pass to matplotlib.pyplot.plot.
            **kwargs: Keyword arguments to pass to matplotlib.pyplot.plot.
        """
        plt.plot(self.times, self.data, *args, **kwargs)
        plt.xlim(max(0., self.times[-1] - width / 2), self.times[-1] + width / 2)

    @property
    def num(self):
        return len(self.data)


class Analysis(object):
    """
    Analysis object for communicating with the analysis app.

    Args:
        interactive (bool): Whether the routine is being run from an interactive python session.
            Only one routine from an interactive Python session is allowed.
            Defaults to False.
        save (bool): Automatically save plots. Defaults to False.
        save_path (str): The path to save plots to. Defaults to the current working directory.
        influx_db: An InfluxDB object.

    Attributes:
        interactive (bool): Whether the routine is being run from an interactive python session.
            Only one routine from an interactive Python session is allowed.
            Defaults to False.
        save (bool): Automatically save plots. Defaults to False.
        save_path (str): The path to save plots to. Defaults to the current working directory.
        data (list): The data to send to the analysis app.
        filename (str): The routine file name.
        data_path (str): The path of the buffer file to write to.
        series (dict): A dictionary of Series objects associated with the analysis.
        num (int): The number of analysis iterations.
        influx_db: An InfluxDB object.
    """
    def __init__(self, interactive=False, save=False, save_path=os.getcwd(), influx_db=None):
        self.data = []
        self.interactive = interactive
        if interactive:
            self.filename = "interactive"
        else:
            frame = inspect.stack()[1]
            self.filename = os.path.basename(frame[0].f_code.co_filename)
        self.data_path = os.path.join(self.get_app_root_path(), "plot_data", os.path.splitext(self.filename)[0])
        self.save = save
        self.save_path = save_path
        self.series = {}
        self.num = 0
        self.influx_db = influx_db

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
        self.num += 1
        if self.influx_db:
            self.influx_db.send(self.series)
        for ser in self.series.values():
            ser.pending = False


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

    def plot(self, name, description="", save_name=None, save=None):
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
            save_name (str): The filename to use for saving the plot.
                Defaults to the plot name and the time.
            save (bool): Overrides the save argument in the analysis object.
        """
        if self.save and save is not False or save is True:
            if not save_name:
                save_name = "%s-%s.png" % (name, datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f"))
            full_save_path = os.path.join(self.save_path, save_name)
            plt.savefig(full_save_path)
        plt.annotate("%s (%s)" % (name, self.filename), xy=(0, 0), xycoords="figure fraction")  # annotate plot with file name and plot name
        # encode the plot as a base64 string
        img = BytesIO()
        plt.savefig(img)
        img.seek(0)
        url = base64.b64encode(img.getvalue()).decode()
        self.data.append(dict(type="plot", file=self.filename, name=name, description=description, url=url))
        plt.clf()

    def init_series(self, name):
        """
        Initialize a series object.

        Args:
            name (str): A name to associate with the Series object.

        Returns:
            The Series object.
        """
        ser = Series(name)
        self.series[name] = ser
        return ser


class InfluxDB(object):
    """
    InfluxDB database object.

    Args:
        name (str): A name to associate with this routine in the InfluxDB database.
        url (str): Database server url.
        port (str): Database port number
        username (str): InfluxDB username.
        pwd (str): InfluxDB password.
        db (str): InfluxDB database name.
        tags (dict): Tags to send to the InfluxDB database.

    Attributes:
        name (str):
    """
    def __init__(self, name, url, port, username, pwd, db, tags={}):
        from influxdb import InfluxDBClient
        self.name = name
        self.client = InfluxDBClient(url, port, username, pwd, db)
        self.tags = tags

    def send(self, series):
        res = self.make_json(series)
        try:
            self.client.write_points([res])
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise OSError("Error uploading to the InfluxDB database. Check the database configuration.")

    def make_json(self, series):
        now = str(datetime.datetime.utcnow())
        fields = {}
        for ser in series:
            if ser.pending and ser.influx:
                fields[ser.name] = ser.data[-1]
        return {"measurement": self.name, "time": now, "fields": fields, "tags": self.tags}
