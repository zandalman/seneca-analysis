
import json, uuid, html
from flask_table import Table, Col


def gen_id(marker, seed):
    """
    Generate a random id for use as a unique HTML id.

    Args:
        marker (str): A string to prepend to the random id to delineate the type of object
            and to ensure that the id does not start with a number.
        seed (str): A seed to use to generate the id.

    Returns:
        The id.
    """
    return marker + uuid.uuid5(uuid.NAMESPACE_DNS, seed).hex


class ParamTable(Table):
    """
    A table class for generating parameter tables using flask_table.

    Attributes:
        name: flask_table Col object for parameter names.
        value: flask_table Col object for parameter names.
    """
    name = Col("Name")
    value = Col("Value")


class Param(object):
    """
    A parameter class for generating parameter tables using flask_table.

    Args:
        name (str): Parameter name.
        value (str): Parameter value.

    Attributes:
        name: Parameter name.
        value: Parameter value.
    """
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Data(object):
    """
    A base class for all data classes.

    Args:
        data (dict): Data dictionary read directly from a buffer file.

    Attributes:
        type (str): Type of data.
        file (str): Name of the file that generated the data.
        name (str): Name associated with the data.
        description (str): A description of the data.
        id (str): An id to associate with the data in the analysis app.
        routine_list_id (str): The id of the file that generated the data in the analysis app.
    """
    def __init__(self, data):
        self.type = data["type"]
        self.file = data["file"]
        self.name = data["name"]
        self.description = data["description"]
        self.id = gen_id("p", "".join([data["type"], data["file"], data["name"]]))
        self.routine_list_id = gen_id("r", self.file)

    def create_routine(self, obj_response):
        """
        Create a routine in the plot list.

        Args:
            obj_response: Sijax object response.

        Yields:
            The updated Sijax object response.
        """
        routine_title_HTML = "<li class='plot-list-routine-title invisible'><b>%s</b></li>" % self.file
        routine_HTML = "<ul class='plot-list-routine' id='%s'>%s</ul>" % (self.routine_list_id, routine_title_HTML)
        obj_response.html_append("#plot-list", routine_HTML)
        yield obj_response

class Plot(Data):
    """
    A plot class which extends the Data class.

    Args:
        plot_data (dict): Data dictionary read directly from a buffer file.

    Attributes:
        url (str): The web url of the plot.
        All attributes of the Data class.
    """
    def __init__(self, plot_data):
        super().__init__(plot_data)
        self.url = "data:image/png;base64,%s" % plot_data["url"]

    def create(self, obj_response):
        """
        Create an item in the plot list and initialize the plot.

        Args:
            obj_response: Sijax object response.

        Yields:
            The updated Sijax object response.
        """
        obj_response.html_append("#plots-container", "<div id='%s' class='plot-container' title='%s' style='display: none;'></div>" % (self.id, self.description))
        obj_response.html_append("#%s" % self.routine_list_id, "<li class='plot-list-item invisible' data-id='%s'>%s - %s</li>" % (self.id, html.escape(self.name), self.type))
        yield obj_response
        obj_response.call("init_img", [self.url, self.id])
        yield obj_response

    def update(self, obj_response):
        """
        Update the plot.

        Args:
            obj_response: Sijax object response.

        Yields:
            The updated Sijax object response.
        """
        obj_response.call("update_img", [self.url, self.id])
        yield obj_response

class Table(Data):
    """
    A table class which extends the Data class.

    Args:
        plot_data (dict): Data dictionary read directly from a buffer file.

    Attributes:
        data (dict): The parameter data for the table.
        caption (str): The table caption which includes the table name and routine name.
        html (str): The html for the table.
        All attributes of the Data class.
    """
    def __init__(self, plot_data):
        super().__init__(plot_data)
        self.data = json.loads(plot_data["data"])
        self.caption = "<caption>%s (%s)</caption>" % (html.escape(self.name), self.file)

    def update(self, obj_response):
        """
        Update the table.

        Args:
            obj_response: Sijax object response.

        Yields:
            The updated Sijax object response.
        """
        obj_response.html("#%s" % self.id, self.html)
        yield obj_response

    def create(self, obj_response):
        """
        Create an item in the plot list and initialize the table.

        Args:
            obj_response: Sijax object response.

        Yields:
            The updated Sijax object response.
        """
        table_container_HTML = "<div class='table-container' id='%s' title='%s' style='display: none;'>%s</div>" % (self.id, self.description, self.html)
        obj_response.html_append("#plots-container", table_container_HTML)
        obj_response.html_append("#%s" % self.routine_list_id, "<li class='plot-list-item invisible' data-id='%s'>%s - table</li>" % (self.id, html.escape(self.name)))
        yield obj_response
        obj_response.call("init_table", [self.id])
        yield obj_response

    @property
    def html(self):
        params = [Param(html.escape(str(key)), html.escape(str(value))) for key, value in sorted(self.data.items())]
        html_list = ParamTable(params).__html__().split()
        html_list.insert(1, self.caption)
        return "".join(html_list)


obj_types = {"plot": Plot, "table": Table, "image": Plot}  # dictionary relating data type string from the buffer files to objects
