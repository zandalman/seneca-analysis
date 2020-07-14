
# import libraries
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import inspect
import os


# set global variables
app_root_path = ""
interactive = False


def end_loop():
    global interactive
    # get the name of the file
    if interactive:
        filename = "interactive"
    else:
        frame = inspect.stack()[1]
        filename = os.path.splitext(os.path.basename(frame[0].f_code.co_filename))[0]
    with open(os.path.join(get_app_root_path(), "plot_data", filename), 'w') as plot_data:
        plot_data.close()


def send_message(message):
    global interactive
    # get the name of the file
    if interactive:
        filename = "interactive"
    else:
        frame = inspect.stack()[1]
        filename = os.path.splitext(os.path.basename(frame[0].f_code.co_filename))[0]
    output_info = "@@@" + "@@@".join([str(info) for info in ["message", filename, "", "", message]])
    write_data(output_info, filename)  # write data to the plot data path
    with open(os.path.join(get_app_root_path(), "plot_data", filename), 'w') as plot_data:
        plot_data.close()


def analysis_complete():
    global interactive
    # get the name of the file
    if interactive:
        filename = "interactive"
    else:
        frame = inspect.stack()[1]
        filename = os.path.splitext(os.path.basename(frame[0].f_code.co_filename))[0]
    output_info = "@@@" + "@@@".join([str(info) for info in ["message", filename, "", "", "Analysis complete!"]])
    write_data(output_info, filename)  # write data to the plot data path



def get_app_root_path():
    """
    Get the app root path

    Return:
        OSError: If app root path has not been configured
            or the configured app root path doesn't exist
            or the configured app root path does not contain a 'plot_data' directory
    """
    global app_root_path
    if not app_root_path:
        message = "App root path not configured. Try 'seneca_analysis.app_root_path = APP_ROOT_PATH'"
        send_message(message)
        raise OSError(message)
    elif not os.path.exists(app_root_path):
        message = "App root path '%s' is not a valid path." % app_root_path
        send_message(message)
        raise OSError(message)
    elif "plot_data" not in os.listdir(app_root_path):
        message = "App root path '%s' does not contain 'plot_data' directory. Check that the app root path has been configured properly." % app_root_path
        send_message(message)
        raise OSError(message)
    else:
        return app_root_path


def write_data(data, filename):
    """
    Write data to the plot data path.

    Args:
        data (str): Data to write
        filename (str): Name of file to write to
    """
    full_path = os.path.join(get_app_root_path(), "plot_data", filename)
    with open(full_path, 'a+') as plot_data:
        plot_data.write(data)


def send_image(name, path, description=""):
    """
    Send an image to the analysis app.

    The function writes the following information to the plot data path
        1. The type of object, in this case "image".
        2. The name of the file where the function is called.
        3. The name argument.
        4. The description argument, if provided.
        5. The base64 encoded string for the image.

        Args:
            name (str): A name to associate with the image in the analysis app.
            path (str): The path to the image file.
            description (str): A description of the image.

        Returns:
            ValueError: If the image path is invalid.
    """
    global interactive
    # get the name of the file
    if interactive:
        filename = "interactive"
    else:
        frame = inspect.stack()[1]
        filename = os.path.splitext(os.path.basename(frame[0].f_code.co_filename))[0]
    if os.path.isfile(path):
        # encode the image as a base64 string
        with open(path, "rb") as image_file:
            image_url = base64.b64encode(image_file.read()).decode()
        output_info = "@@@" + "@@@".join([str(info) for info in ["image", filename, name, description, image_url]])
        write_data(output_info, filename) # write data to the plot data path
    else:
        raise FileNotFoundError("'%s' is not a valid file path." % path)


def send_table(name, data, description=""):
    """
    Send a table to the analysis app.

    The function writes the following information to the plot data path
        1. The type of object, in this case "table".
        2. The name of the file where the function is called.
        3. The name argument.
        4. The description argument, if provided.
        5. The data argument encoded as a json string if the argument is a dictionary.

            Args:
                name (str): A name to associate with the image in the analysis app.
                data (dict): The data to send to the analysis app.
                description (str): A description of the image.
        """
    global interactive
    # get the name of the file
    if interactive:
        filename = "interactive"
    else:
        frame = inspect.stack()[1]
        filename = os.path.splitext(os.path.basename(frame[0].f_code.co_filename))[0]
    # if function output is dictionary, encode it as a json string
    if type(data) != dict:
        data = "{}"
    else:
        data = json.dumps(data)
    output_info = "@@@" + "@@@".join([str(info) for info in ["table", filename, name, description, data]])
    write_data(output_info, filename)  # write data to PLOT_DATA_PATH


def send_current_plot(name, description=""):
    """
    Send the current matplotlib plot to the analysis app.

    The function writes the following information to the plot data path
        1. The type of object, in this case "plot".
        2. The name of the file where the function is called.
        3. The name argument.
        4. The description argument, if provided.
        5. The base64 encoded string for the generated matplotlib plot.

    Args:
        name (str): A name to associate with the image in the analysis app.
        description (str): A description of the image.
    """
    global interactive
    # get the name of the file
    if interactive:
        filename = "interactive"
    else:
        frame = inspect.stack()[1]
        filename = os.path.splitext(os.path.basename(frame[0].f_code.co_filename))[0]
    plt.annotate("%s (%s)" % (filename, name), xy=(0, 0), xycoords='figure fraction')  # annotate plot with file name and plot name
    # encode the plot as a base64 string
    img = BytesIO()
    plt.savefig(img)
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    output_info = "@@@" + "@@@".join([str(info) for info in ["plot", filename, name, description, plot_url]])
    write_data(output_info, filename)  # write data to the plot data path
    plt.clf()
