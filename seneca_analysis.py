
# import libraries
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import inspect
import os


# set global variables
APP_ROOT_PATH = "/Users/zacharyandalman/PycharmProjects/analysis"
PLOT_DATA_PATH = os.path.join(APP_ROOT_PATH, "plot_data", "plot_data")


def write_data(data):
    """
    Write data to PLOT_DATA_PATH.

    Args:
        data (str): Data to write
    """
    with open(PLOT_DATA_PATH, 'w') as plot_data:
        plot_data.write(data)


def plot(interactive=False, multiple=False):
    """
    Generate a decorator which links matplotlib functions to the analysis app.

    Args:
        interactive (bool): Set to 'True' if using an interactive Python session.
            Only one interactive session may be used at a time.
        multiple (bool): Set to 'True' if using the wrapped function multiple times per loop.
            Pass 'reset=True' to the first call of wrapped function in loop.

    Returns:
        A decorator which links matplotlib functions to the analysis app.
    """
    def plot_decorator(func):
        """
        A decorator which links matplotlib functions to the analysis app.

        Args:
            func: The matplotlib function to decorate.

        Returns:
            The decorated matplotlib function.
        """
        def plot_wrapper(*args, **kwargs):
            """
            A wrapper which links matplotlib functions to the analysis app.

            If the function returns a dictionary, the wrapper will send the data to the analysis app to be displayed as a data table.
            The wrapped function writes the following information to PLOT_DATA_PATH
                1. The type of object, in this case "plot".
                2. The name of the file where the function is called.
                3. The name of the function.
                4. The docstring of the function.
                5. The counter attribute.
                6. The base64 encoded string for the generated matplotlib plot.
                7. The return of the function encoded as a json string if the function returns a dictionary.

            Args:
                *args: Arguments passed to the wrapped function.
                **kwargs: Keyword arguments passed to the wrapped function.
                    If 'reset=True' is a keyword argument, it will reset the counter attribute to zero.

            Attributes:
                counter (int): The number of times the function has been called in the loop.
                    Always zero if 'multiple' is 'False.'

            Returns:
                Whatever the wrapped function returns.
            """
            if multiple:
                reset = kwargs.pop("reset", False)
                if not reset:
                    plot_wrapper.counter += 1 # increment counter
            plt.close() # close any open plots
            data = func(*args, **kwargs) # run the matplotlib function
            # get the name of the file
            if interactive:
                filename = "interactive"
            else:
                frame = inspect.stack()[1]
                filename = os.path.basename(frame[0].f_code.co_filename)
            plt.annotate("%s (%s)" % (filename, func.__name__), xy=(0, 0), xycoords='figure fraction') # annotate plot with file name and function name
            # if function output is dictionary, encode it as a json string
            if type(data) != dict:
                data = "{}"
            else:
                data = json.dumps(data)
            # encode the plot as a base64 string
            img = BytesIO()
            plt.savefig(img)
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()
            output_info = "@@@" + "@@@".join([str(info) for info in ["plot", filename, func.__name__, func.__doc__, plot_wrapper.counter, plot_url, data]])
            write_data(output_info) # write data to PLOT_DATA_PATH
            return data
        plot_wrapper.counter = 0 # initialize counter
        # include wrapped function docstring in wrapper docstring
        if func.__doc__:
            plot_wrapper.__doc__ += func.__doc__
        return plot_wrapper
    return plot_decorator


def table(interactive=False, multiple=False):
    """
    Generate a decorator which links functions to the analysis app.

    Args:
        interactive (bool): Set to 'True' if using an interactive Python session.
            Only one interactive session may be used at a time.
        multiple (bool): Set to 'True' if using the wrapped function multiple times per loop.
            Pass 'reset=True' to the first call of wrapped function in loop.

    Returns:
        A decorator which links functions to the analysis app.
    """
    def table_decorator(func):
        """
        A decorator which links functions to the analysis app.

        Args:
            func: The function to decorate.

        Returns:
            The decorated function.
        """
        def table_wrapper(*args, **kwargs):
            """
            A wrapper which links functions to the analysis app.

            If the function returns a dictionary, the wrapper will send the data to the analysis app to be displayed as a data table.
            The wrapped function writes the following information to PLOT_DATA_PATH
                1. The type of object, in this case "table".
                2. The name of the file where the function is called.
                3. The name of the function.
                4. The docstring of the function.
                5. The counter attribute.
                6. The return of the function encoded as a json string if the function returns a dictionary.

                Args:
                    *args: Arguments passed to the wrapped function.
                    **kwargs: Keyword arguments passed to the wrapped function.
                        If 'reset=True' is a keyword argument, it will reset the counter attribute to zero.

                Attributes:
                    counter (int): The number of times the function has been called in the loop.
                        Always zero if 'multiple' is 'False.'

                Returns:
                    Whatever the wrapped function returns.
            """
            if multiple:
                reset = kwargs.pop("reset", False)
                if not reset:
                    table_wrapper.counter += 1 # increment counter
            data = func(*args, **kwargs) # run the function
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
            output_info = "@@@" + "@@@".join([str(info) for info in ["table", filename, func.__name__, func.__doc__, table_wrapper.counter, "", data]])
            write_data(output_info) # write data to PLOT_DATA_PATH
            return data
        table_wrapper.counter = 0 # initialize counter
        # include wrapped function docstring in wrapper docstring
        if func.__doc__:
            table_wrapper.__doc__ += func.__doc__
        return table_wrapper
    return table_decorator


def image(name, path, interactive=False, description=""):
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
            description (str): A description of the

        Returns:
            True: If the image path is valid.
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
        output_info = "@@@" + "@@@".join([str(info) for info in ["image", filename, name, description, 0, image_url, "{}"]])
        write_data(output_info) # write data to PLOT_DATA_PATH
        return True
    else:
        raise ValueError("'%s' is not a valid file path." % path)
