from flask_server.models.db_models_SDSP_Services import *
from flask_server.models.db_models_RMS import *
from flask_server.models.db_models_BMS import *
from flask_server import app
from geoalchemy2.shape import to_shape 
from csv import reader
from datetime import datetime


# Convert to an int but assign blank strings to be 0
def safeInt(i):
    i = i.strip()
    return int(i) if i else 0

# Convert to an int but assign blank strings to be 0
def safeFloat(f):
    f = f.strip()
    return float(f) if f else 0.0