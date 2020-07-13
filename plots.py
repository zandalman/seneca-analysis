
import json, html

def html_sanitize(string):
    invalid_chars = ["~", "!", "@", "$", "%", "^", "&", "*", "(", ")", "+", "=", ",", ".", "/", "'", ";", ":", '"', "?", ">", "<", "[", "]", "\\", "{", "}", "|", "`", "#"]
    for char in invalid_chars:
        string = string.replace(char, "-")
    return string

# remove all plots and data tables
def remove_plots(obj_response):
    obj_response.html("#plots-container, #plot-list", "")

class Data(object):

    def __init__(self, data):
        self.type = data[0]
        self.file = data[1]
        self.name = data[2]
        self.description = data[3]
        self.id = html_sanitize("-".join(data[:3]))

    def create_routine(self, obj_response):
        routine_title_HTML = "<li class='plot-list-routine-title invisible'><b>%s</b></li>" % html.escape(self.file)
        routine_HTML = "<ul class='plot-list-routine' id='plot-list-%s'>%s</ul>" % (html_sanitize(self.file), routine_title_HTML)
        obj_response.html_append("#plot-list", routine_HTML)
        yield obj_response

class Plot(Data):

    def __init__(self, plot_data):
        super.__init__(plot_data)
        self.url = "data:image/png;base64,%s" % plot_data[4]

    def create(self, obj_response):
        obj_response.html_append("#plots-container", "<div id='%s' class='plot-container' title='%s' style='display: none;'></div>" % (self.id, self.description))
        obj_response.html_append("#plot-list-%s" % html_sanitize(self.file), "<li class='plot-list-item invisible' data-id='%s'>%s - %s</li>" % (self.id, html.escape(self.name), self.type))
        yield obj_response
        obj_response.call("init_img", [self.url, self.id])
        yield obj_response

    def update(self, obj_response):
        obj_response.call("update_img", [self.url, self.id])
        yield obj_response

class Table(Data):

    def __init__(self, plot_data):
        super.__init__(plot_data)
        self.data = json.loads(plot_data[4])
        self.caption = caption = "<caption>%s (%s)</caption>" % (html.escape(self.name), html.escape(self.file))

    def generate_table_HTML(self):
        table_body_HTML = ""
        for param in sorted(self.data.keys()):
            table_body_HTML += "<tr><th>%s</th><td>%s</td></tr>" % (html.escape(param), html.escape(self.data[param]))
        table_HTML = "<table>%s<tbody>%s</tbody></table>" % (self.caption, table_body_HTML)
        return table_HTML

    def update(self, obj_response):
        obj_response.html("#%s-table" % self.id, self.generate_table_HTML())
        yield obj_response

    def create(self, obj_response):
        table_container_HTML = "<div class='table-container' id='%s-table' title='%s' style='display: none;'>%s</div>" % (self.id, self.description, self.generate_table_HTML())
        obj_response.html_append("#plots-container", table_container_HTML)
        obj_response.html_append("#plot-list-%s" % html_sanitize(self.file), "<li class='plot-list-item invisible' data-id='%s-table'>%s - table</li>" % (self.id, html.escape(self.name)))
        yield obj_response
        obj_response.call("init_table", ["%s-table" % self.id])
        yield obj_response

obj_types = {"plot": Plot, "table": Table, "image": Plot}

