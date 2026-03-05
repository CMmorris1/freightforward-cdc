FROM python:3.11-slim

WORKDIR /flask_app

# Copy and install requiremnts
COPY requirements.txt .
RUN  pip3 install -r requirements.txt

# Copy all other files in this directory
COPY . .

# Expose port 5000 for Flask/Gunicorn
EXPOSE 5000

# Run the Flask API with the Gunicorn server and logging of flask and access errors
CMD ["/bin/sh", "-c", "gunicorn -w 1 --timeout=300 --bind 0.0.0.0:5000 --log-level=error --access-logfile=./logs/API_access.log --error-logfile=./logs/API_error.log wsgi:app >> ./logs/flask_error.log"]