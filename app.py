
# import modules
from flask import Flask, render_template, g
import flask_sijax
from sijax_handlers import *


def init_db():
    """
    Initialize the SQLAlchemy database.

    Returns:
        The log file path and a dictionary of routine names and ids.
    """
    db.create_all()  # load database models
    filenames = os.listdir(app.config["UPLOAD_FOLDER"])
    routines_dict = {}
    for filename in filenames:
        if get_objects(Routine, count=True, name=filename) == 0:
            # add new routines to the database
            routine = Routine(app.config["UPLOAD_FOLDER"], filename)
            db.session.add(routine)
        else:
            routine = get_objects(Routine, name=filename)[0]
        routines_dict[routine.file_id] = routine.name
    if get_objects(Misc, count=True) == 0:
        # initialize a Misc object if none exist
        db.session.add(Misc())
        log_path = None
    else:
        log_path = get_objects(Misc)[0].log_path
    return log_path, routines_dict


def create_app():
    """
    Create the flask app.

    Returns:
        The flask app.
    """
    app = Flask(__name__) # initialize the app.
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
    flask_sijax.Sijax(app)  # initialize flask-sijax
    db.init_app(app)  # initialize the database

    @flask_sijax.route(app, '/')
    def main():
        """
        Render the main page.

        Returns:
            The rendered html template for the main page.
        """
        # initialize the database
        log_path, routines_dict = init_db()
        db.session.commit()
        form_init_js = g.sijax.register_upload_callback("add-routine-form", SijaxUploadHandlers(app).add_routine) # Register Sijax upload handlers
        if g.sijax.is_sijax_request:
            g.sijax.register_object(SijaxHandlers(app))  # Register Sijax handlers
            g.sijax.register_comet_object(SijaxCometHandlers(app))  # Register Sijax comet handlers
            return g.sijax.process_request()
        return render_template("main.html", form_init_js=form_init_js, log_path=log_path, routines=routines_dict)  # Render template
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(threaded=True, debug=True) # run the flask app
