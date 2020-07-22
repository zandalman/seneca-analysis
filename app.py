
# import modules
from flask import Flask, render_template, g
import flask_sijax
from sijax_handlers import *


def init_db():
    filenames = os.listdir(app.config["UPLOAD_FOLDER"])
    routines_dict = {}
    for filename in filenames:
        if get_routines(name=filename) is None:
            routine = Routine(app.config["UPLOAD_FOLDER"], filename)
            db.session.add(routine)
        else:
            routine = get_routines(name=filename)
        routines_dict[routine.file_id] = routine.name
    Misc.query.delete()
    db.session.add(Misc())
    return routines_dict


def create_app():
    app = Flask(__name__)
    # configure flask
    app.config.update(
        SIJAX_STATIC_PATH=os.path.join('.', os.path.dirname(__file__), "static/js/sijax/"),
        SIJAX_JSON_URI="/static/js/sijax/json2.js",
        UPLOAD_FOLDER=os.path.join(app.root_path, "uploads"),
        PLOT_DATA_FOLDER=os.path.join(app.root_path, "plot_data"),
        SESSION_TYPE="sqlalchemy",
        SQLALCHEMY_DATABASE_URI="sqlite:///%s" % os.path.join(app.root_path, "data.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=True
    )
    flask_sijax.Sijax(app) # add flask-sijax
    db.init_app(app) # initialize the database
    app.app_context().push()
    db.create_all()

    @flask_sijax.route(app, '/')
    def main():
        """Generate the main page."""
        # initialize the database
        routines_dict = init_db()
        db.session.commit()
        # Register Sijax upload handlers
        form_init_js = ''
        form_init_js += g.sijax.register_upload_callback("add-routine-form", SijaxUploadHandlers(app).add_routine)
        if g.sijax.is_sijax_request:
            g.sijax.register_object(SijaxHandlers(app))  # Register Sijax handlers
            g.sijax.register_comet_object(SijaxCometHandlers(app))  # Register Sijax comet handlers
            return g.sijax.process_request()
        return render_template("main.html", form_init_js=form_init_js, routines=routines_dict)  # Render template
    return app


app = create_app()
app.run(threaded=True, debug=True) # run the flask app with threads in debug mode
