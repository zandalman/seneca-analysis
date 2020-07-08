
# create and initialize a plot and associated data table
def create_plot(obj_response, plot):
    plot_id = "%s-%s-%s" % (plot["file"].replace(".", "-"), plot["name"], plot["counter"])
    if plot["type"] in ["plot", "image"]:
        obj_response.html_append("#plots-container", "<div id='%s' class='plot-container' title='%s' style='display: none;'></div>" % (plot_id, plot["description"]))
        obj_response.html_append("#plot-list-%s" % plot["file"].replace(".", "-"), "<li class='plot-list-item invisible' data-id='%s'>%s - %s</li>" % (plot_id, plot["name"], plot["type"]))
        yield obj_response
        obj_response.call("init_img", [plot["url"], plot_id])
    if plot["data"]:
        caption = "<caption>%s (%s)</caption>" % (plot["file"], plot["name"])
        plot_table_body = ""
        for param in sorted(plot["data"].keys()):
            plot_table_body += "<tr><th>%s</th><td>%s</td></tr>" % (param, plot["data"][param])
        plot_table = "<div class='table-container' id='%s-table' title='%s' style='display: none;'><table>%s<tbody>%s</tbody></table></div>" % (plot_id, plot["description"], caption, plot_table_body)
        obj_response.html_append("#plots-container", plot_table)
        obj_response.html_append("#plot-list-%s" % plot["file"].replace(".", "-"), "<li class='plot-list-item invisible' data-id='%s-table'>%s - table</li>" % (plot_id, plot["name"]))
        yield obj_response
        obj_response.call("init_table", ["%s-table" % plot_id])
    yield obj_response


# add a routine to the plot list
def create_routine(obj_response, routine_name):
    routine_title_HTML = "<li class='plot-list-routine-title invisible'><b>%s</b></li>" % routine_name
    obj_response.html_append("#plot-list", "<ul class='plot-list-routine' id='plot-list-%s'>%s</ul>" % (routine_name.replace(".", "-"), routine_title_HTML))
    yield obj_response


# update a plot and associated data table
def update_plot(obj_response, plot):
    plot_id = "%s-%s-%s" % (plot["file"].replace(".", "-"), plot["name"], plot["counter"])
    if plot["type"] in ["plot", "image"]:
        obj_response.call("update_img", [plot["url"], plot_id])
    if plot["data"]:
        caption = "<caption>%s (%s)</caption>" % (plot["file"], plot["name"])
        plot_table_body = ""
        for param in sorted(plot["data"].keys()):
            plot_table_body += "<tr><th>%s</th><td>%s</td></tr>" % (param, plot["data"][param])
        plot_table = "<table>%s<tbody>%s</tbody></table>" % (caption, plot_table_body)
        obj_response.html("#%s-table" % plot_id, plot_table)
    yield obj_response


# remove all plots and data tables
def remove_plots(obj_response):
    obj_response.html("#plots-container, #plot-list", "")
