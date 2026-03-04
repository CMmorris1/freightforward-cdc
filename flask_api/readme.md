# SDSP Gateway and Authentication Service
This service will act as the API Gateway that sits in front of the Supplemental Data Service Providers (SDSPs). 
Developers who want to utilize data from the SDSPs within their applications will need to register 
them with the SDSP Gateway. Each application registered will receive an API key, required for 
requesting data. The SDSPs utilize JSON web token authentication, and this service provides temporary 
tokens to all applications with a valid API key. 

The SDSP Gateway consists of a database and server code, written with the Flask microframework for python.  

## Requirements
The following tools and packages are being used specific versions can be seen in [requirements.txt] 

* Python 3: https://www.python.org/
  * Server code is written in python
* Flask: http://flask.palletsprojects.com/en/1.1.x/
  * Microframework used for web-application development
* Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/en/2.x/
  * Object Relational-Mapping (ORM) style interface between flask application and the relational database
* Flask-WTF: https://flask-wtf.readthedocs.io/en/stable/
    * Object-Oriented form creation for flask
* Flask-Login: https://flask-login.readthedocs.io/en/latest/
    * User-session management for flask

## Installation and Getting Started  
The following steps describe how to properly install and configure an environment for running the webserver.  

### Adding security certs and keys
1. Copy the sdsp-servers.crt, sdsp-servers.key, and root_ca.pem files to the 
flask_microframework directory at /home/smartcity-larc/gateway/Server/Gateway/src/flask_microframework
2. With sudo, change the copied files group to smartcity_larc. Ex: sudo chgrp smartcity_larc root_ca.pem
3. With sudo, change the copied filed permissions to 775. Ex: sudo chmod 775 root_ca.pem 

### Environment Setup  
It is recommended that a python virtual environment is configured and used to deploy the webserver. 
This ensure that only dependencies needed for this application are installed.  
1. Setup a virtual environment, run this command from within [flask_microframework] 
folder: `python3 -m venv .env`. 
2. Activate the virtual environment run the commands:  `source env/bin/activate`. 
You should see `(env)` precede your username. To leave the virtual environment 
enter the command: `deactivate`. 
3. Use the [requirements.txt] to install the required packages and dependencies. 
This can be done using the command: `pip3 install -r requirements.txt`.

# Environment Setup Notes
There could be issues installing psycopg2, these are typically related to having the 
postgres database properly installed.  See the database setup section for more details.
There could be issues installing packages due to the requirements specifying a version 
of a package this isn't accessible via pip3.  Lower the version number to one that is accessible 
and check to see if there are any errors after completing the setup.

### Database Setup  
This webserver connects to a postgres database to store battery information. 
Use the readme file at /home/smartcity-larc/gateway/Database/readme.md for more information on 
installing and setting up the postgres database on a machine.

### Configure Environment Variables  
Environment variables need to be set prior to running the webserver. These can be set by setting 
the variables from within the [set_flask_variables.sh] and running the script with the command 
`source ./set_flask_variables.sh`
  
A unique key should be generated for the **AUTH_FLASK_APP_SECRET_KEY** variable. 
This can be done using the python command interpreter:
* From the terminal enter the command: `python3`
* From the python command interpreter, enter the following commands:  
  * `from uuid import uuid4`
  * `uuid4().hex`  
  * Copy the key the key string that is returned (do not include the quotes)
  * enter `exit()` to leave the python interpreter 
  
You can copy and paste the generated key into the *set_flask_variables.sh* script.

The webserver should now be properly configured.
  
## Running the webserver

# Debug #
After creating the environment, entering the environment, installing the requirements, 
and setting the flask variables; the server can be started using the following command within:
/home/smartcity-larc/gateway/Server/Gateway/src/flask_microframework

`python3 wsgi.py`  *DEBUG ONLY*

This will start the built-in flask werkzerg server for debug mode.

# Production #
For production use, the server should be started using the systemd service file located at:
/usr/lib/systemd/system/launch_smartcity_larc_gateway.service

This service file runs the shell script file:
/usr/share/smartcity_larc/launch_gateway.sh

After starting the server the end user's will be able to access data locally using the following url:
You will then be able to access any created routes on the webserver by entering the host address 
with port number, and route name into a webbrowser (i.e. http://localhost:8000/SDSP_Services/V1\<your-route-here\>).

In order to access the data from outside the server, the end user must access the service through
the secure NginX port at: http://certainroc.ndc.nasa.gov:443/SDSP_Services/V1\<your-route-here\>

## Running the Heartbeat Script

For debug mode:
Execute the following command: `python3 mqtt_heartbeat.py` in a separate terminal.

Production:
For production use, the server should be started using the systemd service file located at:
/usr/lib/systemd/system/launch_smartcity_larc_mqtt_heartbeats.service

This service file runs the shell script file:
/usr/share/smartcity_larc/launch_mqtt_heartbeats.sh

## Logging Information ##

Gateway access, error, and flask output logs can be found at /home/smartcity-larc/gateway/Logs when
running in production mode.
