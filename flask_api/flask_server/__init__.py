from flask import Flask
from sys import exit
from jinja2 import select_autoescape
import sqlalchemy
import os

first_request_done = False

def setup_app(app):
    from flask_server.models.freight_db_models import db

    @app.before_request
    def create_tables():
        global first_request_done
        if not first_request_done:

            engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI']) # connect to postgres server
            
            # Create tables if they don't exist
            # db.create_all()

            first_request_done = True

    db.init_app(app)

# Initialize Flask app with critical variables
app = Flask(__name__)

app.jinja_env.autoescape = select_autoescape(       
    default_for_string=True,         
    default=True       
)

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

app.config['SQLALCHEMY_ECHO'] = True

if 'FLASK_RUN_HOST' in os.environ:
    app.config['FLASK_RUN_HOST'] = os.environ['FLASK_RUN_HOST']
else:
    print("\nERROR: 'FLASK_RUN_HOST' environment variable needs to be set.")
    exit()

if 'FLASK_RUN_PORT' in os.environ:
    app.config['FLASK_RUN_PORT'] = int(os.environ['FLASK_RUN_PORT'])
else:
    print("\nERROR: 'FLASK_RUN_PORT' environment variable needs to be set.")
    exit()

if 'FLASK_DEBUG' in os.environ:
    app.config['FLASK_DEBUG'] = int(os.environ['FLASK_DEBUG'])
else:
    print("\nERROR: 'FLASK_DEBUG' environment variable needs to be set.")
    exit()

if 'SQLALCHEMY_DATABASE_URI' in os.environ:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
else:
    print("\nERROR: 'SQLALCHEMY_DATABASE_URI' environment variable needs to be set.")
    exit()

if 'DATABASE_SCHEMA' in os.environ:
    app.config['DATABASE_SCHEMA'] = os.environ['DATABASE_SCHEMA']
else:
    print("\nERROR: 'SQLALCHEMY_DATABASE_URI' environment variable needs to be set.")
    exit()

if 'HTTPS_ENABLED' in os.environ:
    app.config['HTTPS_ENABLED'] = int(os.environ['HTTPS_ENABLED'])

    if app.config['HTTPS_ENABLED'] == 1:
        if 'VERIFY_USER' in os.environ:
            app.config['VERIFY_USER'] = int(os.environ['VERIFY_USER'])
        else:
            print("\nERROR: 'VERIFY_USER' environment variable needs to be set.")
            exit()
else:
    print("\nERROR: 'HTTPS_ENABLED' environment variable needs to be set.")
    exit()

setup_app(app)

# from  flask_server.routes import *
from  flask_server.routes.freight_CRUD_routes import *