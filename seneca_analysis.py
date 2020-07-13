
# import libraries
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import inspect
import os


# set global variables
APP_ROOT_PATH = "/Users/zacharyandalman/PycharmProjects/analysis/plot_data"
PLOT_DATA_PATH = os.path.join(APP_ROOT_PATH, "plot_data")


def write_data(data):
    """
    Write data to PLOT_DATA_PATH.

    Args:
        data (str): Data to write
    """
    with open(PLOT_DATA_PATH, 'w') as plot_data:
        plot_data.write(data)


def send_image(name, path, interactive=False, description=""):
    """
    Send an image to the analysis app.

    The function writes the following information to PLOT_DATA_PATH
        1. The type of object, in this case "image".
        2. The name of the file where the function is called.
        3. The name argument.
        4. The description argument, if provided.
        5. The base64 encoded string for the image.

        Args:
            name (str): A name to associate with the image in the analysis app.
            path (str): The path to the image file.
            interactive (bool): Set to 'True' if using an interactive Python session.
                Only one interactive session may be used at a time.
            description (str): A description of the image.

        Returns:
            ValueError: If the image path is invalid.
    """
    # get the name of the file
    if interactive:
        filename = "interactive"
    else:
        frame = inspect.stack()[1]
        filename = os.path.basename(frame[0].f_code.co_filename)
    if os.path.isfile(path):
        # encode the image as a base64 string
        with open(path, "rb") as image_file:
            image_url = base64.b64encode(image_file.read()).decode()
        output_info = "@@@" + "@@@".join([str(info) for info in ["image", filename, name, description, image_url]])
        write_data(output_info) # write data to PLOT_DATA_PATH
    else:
        raise ValueError("'%s' is not a valid file path." % path)


def send_table(name, data, interactive=False, description=""):
    """
    Send a table to the analysis app.

    The function writes the following information to PLOT_DATA_PATH
        1. The type of object, in this case "table".
        2. The name of the file where the function is called.
        3. The name argument.
        4. The description argument, if provided.
        5. The data argument encoded as a json string if the argument is a dictionary.

            Args:
                name (str): A name to associate with the image in the analysis app.
                data (dict): The data to send to the analysis app.
                interactive (bool): Set to 'True' if using an interactive Python session.
                    Only one interactive session may be used at a time.
                description (str): A description of the image.
        """
    # get the name of the file
    if interactive:
        filename = "interactive"
    else:
        frame = inspect.stack()[1]
        filename = os.path.basename(frame[0].f_code.co_filename)
    # if function output is dictionary, encode it as a json string
    if type(data) != dict:
        data = "{}"
    else:
        data = json.dumps(data)
    output_info = "@@@" + "@@@".join([str(info) for info in ["table", filename, name, description, data]])
    write_data(output_info)  # write data to PLOT_DATA_PATH


def send_current_plot(name, interactive=False, description=""):
    """
    Send the current matplotlib plot to the analysis app.

    The function writes the following information to PLOT_DATA_PATH
        1. The type of object, in this case "plot".
        2. The name of the file where the function is called.
        3. The name argument.
        4. The description argument, if provided.
        5. The base64 encoded string for the generated matplotlib plot.

    Args:
        name (str): A name to associate with the image in the analysis app.
        interactive (bool): Set to 'True' if using an interactive Python session.
            Only one interactive session may be used at a time.
        description (str): A description of the image.
    """
    # get the name of the file
    if interactive:
        filename = "interactive"
    else:
        frame = inspect.stack()[1]
        filename = os.path.basename(frame[0].f_code.co_filename)
    plt.annotate("%s (%s)" % (filename, name), xy=(0, 0), xycoords='figure fraction')  # annotate plot with file name and plot name
    # encode the plot as a base64 string
    img = BytesIO()
    plt.savefig(img)
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    output_info = "@@@" + "@@@".join([str(info) for info in ["plot", filename, name, description, plot_url]])
    write_data(output_info)  # write data to PLOT_DATA_PATH
    plt.clf()


#def analysis_complete():