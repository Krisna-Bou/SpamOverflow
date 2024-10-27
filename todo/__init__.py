from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os, shutil

def create_app(config_overrides=None):

    # if os.path.isfile("instance/db.sqlite"):
    #     os.remove("instance/db.sqlite")
    app = Flask(__name__)
    app.json.sort_keys = False

    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite"
    if config_overrides:
        app.config.update(config_overrides)

    # Load the models
    from todo.models import db
    from todo.models.todo import Todo

    db.init_app(app)
    # Create the database tables
    with app.app_context():
        db.create_all()
        db.session.commit()
    # Register the blueprints
    from todo.views.routes import api
    app.register_blueprint(api)
    return app