# Flask API
This API service will service the PostgreSQL freightjobs database, and provices a service to developers by graniting them access to CREATE, READ, UPDATE, and DELETE (CRUD) the Job, Job History, Shipment, Freight, Invoice, and Purchase Order tables located within the database. 


Thid file directory consists of a database and server code, written with the Flask microframework for python.  

## Requirements
The following tools and packages are being used can be seen in [requirements.txt] 

* Python 3: https://www.python.org/
  * Server code is written in python

* Flask: https://flask.palletsprojects.com/en/stable/
  * Microframework used for web-application development

* Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/en/stable/
  * Object Relational-Mapping (ORM) style interface between flask application and the relational database
  
* Flask-WTF: https://flask-wtf.readthedocs.io/en/stable/
    * Object-Oriented form creation for flask

## Installation and Getting Started  
The following steps describe how to properly install and configure an environment for running the webserver.  

### Environment Setup  
It is recommended that a python virtual environment is configured and used to deploy the webserver. 
This ensure that only dependencies needed for this application are installed. 

1. Setup a virtual environment
    - Run this command from within [flask_api] folder: 
    
    `python3 -m venv .env`. 

2. Activate the virtual environment run the commands:  

    `source env/bin/activate`. 

    - You should see `(env)` precede your username. To leave the virtual environment enter the command: `deactivate`

3. Use the [requirements.txt] to install the required packages and dependencies. 
    - This can be done using the command: 
    
    `pip3 install -r requirements.txt`

4. If running locally, environment variables need to be set prior to running the webserver. These can be set by setting the variables from within the [set_flask_variables.sh] and running the script with the command:

    `source ./set_flask_variables.sh`

# Environment Setup Notes
There could be issues installing psycopg2, these are typically related to having the 
postgres database properly installed.  See the database setup section for more details.
There could be issues installing packages due to the requirements specifying a version 
of a package this isn't accessible via pip3.  Lower the version number to one that is accessible 
and check to see if there are any errors after completing the setup.

### Database Setup  
This webserver connects to a postgres database to store freight shipping information. The database can be run locally or in Terraform. See top level README.md for loacl and make run setups.  

## Running the webserver

# Debug #
After creating the environment, entering the environment, installing the requirements, 
and setting the flask variables; the server can be started using the following command within the flask_api directory:

`python3 wsgi.py`  *DEBUG ONLY*

This will start the built-in flask werkzerg server for debug mode which is the current recommended mode for demo purposes. This can be changed to production once a better servr stack is installed such as NginX -> Gunicon -> Flask -> PostgreSQL.

# Routes #

An example test python script can be found in the /flask_api/testing directory. It should be modified to fit the testers needs.
