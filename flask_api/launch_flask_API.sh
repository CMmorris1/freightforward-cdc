#!/bin/bash
shopt -s expand_aliases
alias activateVENV="source env/bin/activate"
alias setENVvars="source ./set_flask_variables.sh"

sleep 2

#Launch Flask API
echo $PWD
activateVENV
setENVvars
exc gunicorn -w 1 --timeout=300 --bind 0.0.0.0:5000 \
		--log-level=error \
		--access-logfile=./logs/API_access.log \
		--error-logfile=./logs/API_error.log \
		wsgi:app  \
		*>> ./logs/flask_error.log

