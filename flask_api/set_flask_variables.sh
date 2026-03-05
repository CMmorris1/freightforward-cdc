#!/bin/bash

# Run this script before starting the flask server with 'flask run' to set needed flask variables

# Set environment variables necessary for the flask server here
export FLASK_APP="wsgi.py"

# Set host address here
export FLASK_RUN_HOST="0.0.0.0"

# Set port here
export FLASK_RUN_PORT="5000"

# Set URI to postgres database here
export SQLALCHEMY_DATABASE_URI="postgresql://de_user:de_password@localhost:5433/freightjobs"
# export SQLALCHEMY_DATABASE_URI="postgresql://materialize@localhost:6875/materialize"
export DATABASE_SCHEMA="public"


# Set HTTPS and SSL Parameters here
export HTTPS_ENABLED=0 # 1 for true, 0 for false
export VERIFY_USER=1 # 1 for true, 0 for false
# export SERVER_CERT="sdsp-servers.crt"
# export SERVER_KEY="sdsp-servers.key"
# export CA_T="root_ca.pem"

# Set debug option here. Use '1' for debug mode, '0' for production mode
export FLASK_DEBUG=1

export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
