from flask_server import app, login_manager
from flask import flash, render_template, url_for, redirect, jsonify, request, Response, session
from flask_server.models.db_models_RFI import *
from flask_server.forms import *
from flask_server.helper_functions.helper_functions_RFI import *
from flask_server.helper_functions.helper_functions_SOPS import *
from flask_server.models.db_models_SDSP_Services import *
from flask_server import app, bcrypt
from flask_talisman import Talisman
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timedelta
from itertools import groupby
from sqlalchemy import and_, or_, not_
from json import load
from flask_login import login_user, current_user, logout_user
from uuid import uuid4
import paho.mqtt.subscribe as subscribe
import requests
import jwt
import logging
import pprint
import json
import matplotlib.patches as patches
import matplotlib.path as mplPath
from time import sleep
import os
import subprocess
import pandas as pd
import datetime

logging.basicConfig(level=logging.DEBUG)

sdsp_name = app.config['AUTH_NAME']
sdsp_version = app.config['AUTH_VERSION']
talisman = Talisman(app)

# =========================== Authentication Decorator ==============================================
# Decorator to verify a user is logged in with an active session
# Accesses the "current_user" flask_login global
# Returns: login validation if true, redirect to login route if false


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You must be logged in to view this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to verify a user has admin priviledges (for admin-specific routes)
# Accesses the "admin" field of the "current_user" flask_login global
# Returns: admin validation if true, redirect to index page if false


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.admin:
            flash('You must be an administrator to view this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        nameFound = 'None'

        try:
            route = request.url
            ip_address = request.remote_addr
            http_method = request.method
            auth_token = (
                request.headers["Authorization"] if "Authorization" in request.headers else None)

            # isolate requested sdsp
            sdsp_route_name = route.split('/', 3)[3].split('/')[0]

            # look up name in auth.registered_sdsp table and see if sdsp_route_name is in name
            sdspNames = [{"id": b.id,
                          "name": b.name,
                          "version": b.version} for b in Registered_SDSP.query.all()]

            # if items returned from query
            if (len(sdspNames) > 0):
                # find if route name was in query
                for row in sdspNames:
                    for key, value in row.items():
                        if (sdsp_route_name in str(value)):
                            nameFound = value

                # if name found, set sdsp_name to found name
                if ('None' not in nameFound):
                    sdsp_name = nameFound

            if not auth_token:
                return jsonify({'message': 'ERROR - Token is missing'}), 401

            if auth_token[0:6].lower() == "bearer":
                auth_token = auth_token[6:]

            jsonBody = {"sdsp_name": sdsp_name, "sdsp_version": sdsp_version,
                        "http_method": http_method, "ip_address": ip_address, "token": auth_token}
            response = requests.post(
                app.config["AUTH_SERVICE_TOKEN_CHECK_URI"], json=jsonBody)
            responseBody = response.json()

            if response.status_code == 400:
                return jsonify({'message': "ERROR - The SDSP encountered an internal error. Please contact the SDSP administrator"}), 500
            if response.status_code != 200:
                return jsonify({'message': responseBody["message"]}), response.status_code

            return f(*args, **kwargs)
        except Exception as e:
            print(e)

    return decorated

# =========================== RFI frequecy Routes ===================================================

##########################
# Freq 900 Kriging Routes:
##########################


@app.route("/RFI/V1/freq900_Kriging=<index>", methods=["GET"])
@token_required
def getfrequ900InfoByIndex(index):

    # Query the freq900 RFI table and build a list of dictionaries for all relavent entries
    freq900Dict_Kriging = [{"index": c.index,
                            "name": c.name,
                            "date": c.date,
                            "source": c.source,
                            "altitude": c.altitude,
                            "level": c.level,
                            "vertex_count": c.vertex_count,
                            "contour_list": c.contour_list
                            } for c in Freq900_Kriging.query.filter_by(index=index).all()]

    if len(freq900Dict_Kriging) > 0:
        response = jsonify({'freq900_Kriging': freq900Dict_Kriging})
        response.status_code = 200
    else:
        message = "No record with a index of '{}' could be found.".format(
            index)
        response = jsonify({'message': message})
        response.status_code = 400

    return response

# Get Freq900_Kriging Contours by Level.


@app.route("/RFI/V1/freq900_Kriging.level=<level>", methods=["GET"])
@token_required
def getfrequ900InfoByLevel(level):

    # Query the freq900 RFI table and build a list of dictionaries for all relavent entries
    freq900Dict_Kriging = [{"index": c.index,
                            "contour_list": c.contour_list
                            } for c in Freq900_Kriging.query.filter_by(level=level).all()]

    if len(freq900Dict_Kriging) > 0:
        response = jsonify({'freq900_Kriging_level': freq900Dict_Kriging})
        response.status_code = 200
    else:
        message = "No record with a level of '{}' could be found.".format(
            level)
        response = jsonify({'message': message})
        response.status_code = 400

    return response

# Get all contours for freq900_Kriging


@app.route("/RFI/V1/freq900_Kriging.contours", methods=["GET"])
@token_required
def getfrequ900Contours():

    # Query the freq900 RFI table and build a list of dictionaries for all relavent entries
    freq900Dict_Kriging = [{
        "contour_list": c.contour_list,
        "level": c.level,
        "altitude": c.altitude
    } for c in Freq900_Kriging.query.filter(and_(
        Freq900_Kriging.level <= 0,
        Freq900_Kriging.level >= -99
    )).all()]

    if len(freq900Dict_Kriging) > 0:
        response = jsonify({'freq900_Kriging_contours': freq900Dict_Kriging})
        response.status_code = 200
    else:
        message = "No records could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response

# Get all contours for a given frequency, tolerance, and buffer.


@app.route("/RFI/V1/freq900_Kriging.freqTolerance=<tolerance>.buffer=<buffer>", methods=["GET"])
@token_required
def getfrequ900KrigingContoursForGivenFrequencyToleranceBuffer(tolerance, buffer):

    # Query the freq900 RFI table and build a list of dictionaries for all relavent entries
    freq900Dict_Kriging = [{
        "contour_list": c.contour_list,
        "level": c.level,
        "altitude": c.altitude
    } for c in Freq900_Kriging.query.filter(and_(
        Freq900_Kriging.level <= (int(tolerance) + int(buffer)),
        Freq900_Kriging.level >= int(tolerance),
        Freq900_Kriging.level <= 0,
        Freq900_Kriging.level >= -99
    )).all()]

    if len(freq900Dict_Kriging) > 0:
        response = jsonify({'freq900_Kriging_contours': freq900Dict_Kriging})
        response.status_code = 200
    else:
        message = "No records could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response

###########################
 # Freq 2400 Kriging Routes:
###########################


@app.route("/RFI/V1/freq2400_Kriging=<index>", methods=["GET"])
@token_required
def getfrequ2400InfoByIndex(index):
    # Query the freq2400 RFI table and build a list of dictionaries for all relavent entries
    freq2400Dict_Kriging = [{"index": c.index,
                             "name": c.name,
                             "date": c.date,
                             "source": c.source,
                             "altitude": c.altitude,
                             "level": c.level,
                             "vertex_count": c.vertex_count,
                             "contour_list": c.contour_list
                             } for c in Freq2400_Kriging.query.filter_by(index=index).all()]

    if len(freq2400Dict_Kriging) > 0:
        response = jsonify({'freq2400_Kriging': freq2400Dict_Kriging})
        response.status_code = 200
    else:
        message = "No record with a index of '{}' could be found.".format(
            index)
        response = jsonify({'message': message})
        response.status_code = 400

    return response

###########################
# Freq 926 WinProp Routes:
###########################


@app.route("/RFI/V1/freq926_WinProp=<index>", methods=["GET"])
@token_required
def getfrequ926InfoByIndex(index):

    # Query the freq900 RFI table and build a list of dictionaries for all relavent entries
    freq926Dict_WinProp = [{"index": c.index,
                            "name": c.name,
                            "date": c.date,
                            "source": c.source,
                            "altitude": c.altitude,
                            "level": c.level,
                            "vertex_count": c.vertex_count,
                            "contour_list": c.contour_list
                            } for c in Freq926_WinProp.query.filter_by(index=index).all()]

    if len(freq926Dict_WinProp) > 0:
        response = jsonify({'freq926_WinProp': freq926Dict_WinProp})
        response.status_code = 200
    else:
        message = "No record with a index of '{}' could be found.".format(
            index)
        response = jsonify({'message': message})
        response.status_code = 400

    return response

# Get freq926_WinProp Contours by Level.


@app.route("/RFI/V1/freq926_WinProp.level=<level>", methods=["GET"])
@token_required
def getfrequ926InfoByLevel(level):

    # Query the freq900 RFI table and build a list of dictionaries for all relavent entries
    freq926Dict_WinProp = [{"index": c.index,
                            "name": c.name,
                            "date": c.date,
                            "source": c.source,
                            "altitude": c.altitude,
                            "level": c.level,
                            "vertex_count": c.vertex_count,
                            "contour_list": c.contour_list
                            } for c in Freq926_WinProp.query.filter_by(level=level).all()]

    if len(freq926Dict_WinProp) > 0:
        response = jsonify({'freq926_WinProp_level': freq926Dict_WinProp})
        response.status_code = 200
    else:
        message = "No record with a level of '{}' could be found.".format(
            level)
        response = jsonify({'message': message})
        response.status_code = 400

    return response

# Get all contours for freq900_Kriging


@app.route("/RFI/V1/freq926_WinProp.contours", methods=["GET"])
@token_required
def getfrequ926Contours():

    # Query the freq900 RFI table and build a list of dictionaries for all relavent entries
    freq926Dict_WinProp = [{
        "index": c.index,
        "name": c.name,
        "date": c.date,
        "source": c.source,
        "altitude": c.altitude,
        "level": c.level,
        "vertex_count": c.vertex_count,
        "contour_list": c.contour_list
    } for c in Freq926_WinProp.query.filter(and_(
        Freq926_WinProp.level <= 0,
        Freq926_WinProp.level >= -99
    )).all()]

    if len(freq926Dict_WinProp) > 0:
        response = jsonify({'freq926_WinProp_contours': freq926Dict_WinProp})
        response.status_code = 200
    else:
        message = "No records could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response

# Get all contours for a given frequency, tolerance, and buffer.


@app.route("/RFI/V1/freq926_WinProp.freqTolerance=<tolerance>.buffer=<buffer>", methods=["GET"])
@token_required
def getfrequ926WinPropContoursForGivenFrequencyToleranceBuffer(tolerance, buffer):

    # Query the freq900 RFI table and build a list of dictionaries for all relavent entries
    freq926Dict_WinProp = [{
        "index": c.index,
        "name": c.name,
        "date": c.date,
        "source": c.source,
        "altitude": c.altitude,
        "level": c.level,
        "vertex_count": c.vertex_count,
        "contour_list": c.contour_list
    } for c in Freq926_WinProp.query.filter(and_(
        Freq926_WinProp.level <= (int(tolerance) + int(buffer)),
        Freq926_WinProp.level >= int(tolerance),
        Freq926_WinProp.level <= 0,
        Freq926_WinProp.level >= -99
    )).all()]

    if len(freq926Dict_WinProp) > 0:
        response = jsonify({'freq926_WinProp_contours': freq926Dict_WinProp})
        response.status_code = 200
    else:
        message = "No records could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response

# =========================== Spectrum Occupency Percentage Routes ===============================================================
# ------------------------------------------------------------------------------------------------------------------------------------------------
# API User login route
# =============================
#   * Serves the "login.html" template with a "LoginForm" object
#   * Once the form has been successfully validated, a new login session is created for the specified user
#
# Extra Decorators:
#   * None
#
# Allowed HTTP Methods:
#   * GET
#   * POST
#
# URL Inputs:
#   * None
#
# Returns:
#   * Redirect to index page
# ------------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/RFI/{}/login/".format(sdsp_version), methods=["GET", "POST"])
def login():

    form = LoginForm()

    # Occurs if no validation errors are raised by the validators on the form object
    if form.validate_on_submit():

        # API User entry looked up based on form's email field data
        apiUser = AOPS_API_User.query.filter_by(email=form.email.data).first()
        passreset = apiUser.passReset

        # Check that password needs reset:
        if passreset:
            return jsonify({'message': "This account has been locked. Needs new password confirmation. Please contact an administrator."}), 401
        else:
            login_user(apiUser)

            return redirect(url_for('index'))

    return render_template('login.html', form=form)

# ------------------------------------------------------------------------------------------------------------------------------------------------
# API User logout route
# =============================
#   * Terminates an API User's session if logged in
#
# Extra Decorators:
#   * None
#
# Allowed HTTP Methods:
#   * None
#
# URL Inputs:
#   * None
#
# Returns:
#   * Redirect to login page
# ------------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/RFI/{}/logout".format(sdsp_version))
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('You have been logged out')

    return redirect(url_for('login'))

# ------------------------------------------------------------------------------------------------------------------------------------------------
# API User registration route
# =============================
#   * Serves the "register.html" template with a "RegistrationForm" object
#   * Once the form has been successfully validated, a new API User object is created and committed to the "auth.api_user" table
#   * A login session is created for the new user
#
# Extra Decorators:
#   * None
#
# Allowed HTTP Methods:
#   * GET
#   * POST
#
# URL Inputs:
#   * None
#
# Returns:
#   * Redirect to index page
# ------------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/RFI/{}/register".format(sdsp_version), methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    # allGroups = [(s.groupname) for s in AOPS_API_User.query.with_entities(AOPS_API_User.groupname)]
    # groupname = list({x.upper() for x in allGroups})

    # Occurs if no validation errors are raised by the validators on the form object
    if form.validate_on_submit():
        # print(form.email.data)
        # Use BCRYPT to generate a password hash from the password form data. Hash is converted to a string to be stored in the table
        passHash = bcrypt.generate_password_hash(
            form.password.data).decode('UTF-8')

        # A new API User object is constructed using the form data and is committed to the database
        newUser = AOPS_API_User(
            email=form.email.data, passHash=passHash, groupname=form.groupname.data.lower())

        db.session.add(newUser)
        db.session.commit()

        # Create a new login session for the user and redirect to the index page. Flash a success message to the user
        login_user(newUser)
        flash('The account was successfully created', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Index route
# =============================
#   * The main route for logged in users
#   * Serves the "index.html" template where API Users can view/edit registered apps and their permissions
#
# Extra Decorators:
#   * login_required
#
# Allowed HTTP Methods:
#   * GET
#
# URL Inputs:
#   * None
#
# Returns:
#   * None
# ------------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/RFI/{}/index".format(sdsp_version), methods=["GET", "POST"])
@login_required
def index():
    obtainChannelList = []
    obtainPercentvehicle_dict = {}
    apiUser = current_user

    regs_vehicles = [(k.id, k.vehiclename, k.groupname, k.location, k.frequencylist, k.channels, k.date_added)
                     for k in Registered_Vehicle.query.filter_by(owner_id=apiUser.id).all()]

    vehicleNames = [(k.vehiclename) for k in Registered_Vehicle.query.filter_by(
        owner_id=apiUser.id).all()]

    # NumberofChannels = regs_vehicles['channels']

    # reqs = []
    #     temp = Registered_App_Permissions.query.filter_by(app_id=key[0]).all()
    #     for perm in temp:
    #         sdsp = Registered_SDSP.query.filter_by(id=perm.sdsp_id).first()
    #         perms.append((key[1], key[2], sdsp.name, perm.allowed_methods, perm.date_granted))

    #     permReqs = Requested_App_Permissions.query.filter_by(app_id=key[0]).all()

    #     for req in permReqs:
    #         reqs.append((Registered_App.query.filter_by(id=req.app_id).first(), req))

    # return render_template('index.html', api_keys=api_keys, perms=perms, reqs=reqs)
    return render_template('index.html', regs_vehicles=sorted(regs_vehicles), vehicleNames=vehicleNames)

# ------------------------------------------------------------------------------------------------------------------------------------------------
# App Registration route
# =============================
#   * API Users can register their applications with the SDSP gateway
#   * Serves the "appRegister.html" template with a "RegisterAppForm" object
#
# Extra Decorators:
#   * login_required
#
# Allowed HTTP Methods:
#   * GET
#   * POST
#
# URL Inputs:
#   * None
#
# Returns:
#   * Redirect to index route upon successful app registration
# ------------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/RFI/{}/register-vehicle".format(sdsp_version), methods=["GET", "POST"])
@login_required
def registerVehicle():
    configFilename = ''
    noConfigdata = {'description': 'No Config File Uploaded'}
    apiUser = current_user

    form = RegisterVehichleForm()

    # Occurs if no validation errors are raised by the validators on the form object
    if form.validate_on_submit():
        existingApp = Registered_Vehicle.query.filter_by(
            vehiclename=form.vehiclename.data, groupname=form.groupname.data).first()

        # Verify the app doesn't already exist with the specified version
        if existingApp:
            flash(
                'A vehicle with the same name and has already been registered by this group.', 'danger')
        else:
            # check if vehicle config file was uploaded during vehicle registration
            if form.configjson.data:
                # obtain uploaded file name
                f = form.configjson.data
                configFilename = secure_filename(f.filename)

                # read stream data
                fileData = f.read()

                # decode string from binary
                json_str = fileData.decode('utf-8')

                # Check if Json string can be converted to json
                isAjson, error, JsonFeedbackInfo = is_configjson(json_str)

                if isAjson:
                    configJSON = json.loads(json_str)
                    frequencylist = list(JsonFeedbackInfo.keys())
                    channelslist = list(JsonFeedbackInfo.values())
                    edit_notes = "N/A"
                    # return render_template('registerVehicle.html', form=form) #DEBUGGUNG
                else:
                    flash("Vehichle Registration Failed - File: " +
                          configFilename + ", Error: " + str(error), 'info')
                    return render_template('registerVehicle.html', form=form)
            else:
                configFilename = "No File Uploaded"
                configJSON = noConfigdata

            # Create a new entry for the app in the rfi.aops_api_vehicles table
            newApp = Registered_Vehicle(
                form.vehiclename.data,
                form.groupname.data.lower(),
                form.location.data,
                apiUser.id,
                datetime.datetime.now(),
                frequencylist,
                channelslist,
                form.notes.data,
                configFilename,
                configJSON,
                datetime.datetime.now(),
                edit_notes,
            )
            db.session.add(newApp)
            db.session.commit()

            return redirect(url_for('index'))

    return render_template('registerVehicle.html', form=form)

# ------------------------------------------------------------------------------------------------------------------------------------------------
# Edit Vehichle Config JSON route
# =============================
#   * API Users can edit the JSON vehichle information uploaded during vehicle registration
#   * Serves the "editConfigJSON.html" template with a "EditJSONForm" object
#
# Extra Decorators:
#   * login_required
#
# Allowed HTTP Methods:
#   * GET
#   * POST
#
# URL Inputs:
#   * None
#
# Returns:
#   * Redirect to index route upon successful app registration
# ------------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/RFI/{}/edit-vehichle/<int:vehicleID>/<string:groupName>".format(sdsp_version), methods=["GET", "POST"])
@login_required
def editVehicle(vehicleID, groupName):
    configFilename = ''
    noConfigdata = {'description': 'No Config File Uploaded'}
    apiUser = current_user

    # obtain vehicle edit
    vehicle = Registered_Vehicle.query.filter(
        Registered_Vehicle.id == vehicleID).first()

    # query current users groups
    Usergroups = [
        s.groupname for s in AOPS_API_User.query.filter_by(id=apiUser.id)]

    # ensure User group names are uppercase
    Usergroups = [x.upper() for x in Usergroups]

    form = EditJSONForm()

    methods = ['Group']
    formChoices = []
    for method in methods:
        choices = AOPS_API_User.query.order_by('id', 'groupname')
        for s in choices:
            if s.groupname.upper() in Usergroups:
                groupTupple = (s.groupname.upper() + '_{}'.format(method),
                               s.groupname.upper() + ' - {}'.format(method))

                if groupTupple not in formChoices:
                    formChoices.append(groupTupple)

    form.groupname.choices = formChoices

    form.vehiclename.data = vehicle.vehiclename

    if request.method == "POST":
        if form.cancel.data:  # if cancel button is clicked, the form.cancel.data will be True
            return redirect(url_for('index'))

        # check if vehicle config file was uploaded during vehicle registration
        if form.configjson.data:
            # obtain uploaded file name
            f = form.configjson.data
            configFilename = secure_filename(f.filename)

            # read stream data
            fileData = f.read()

            # decode string from binary
            json_str = fileData.decode('utf-8')

            # Check if Json string can be converted to json
            isAjson, error, JsonFeedbackInfo = is_configjson(json_str)

            if isAjson:
                configJSON = json.loads(json_str)
                frequencylist = list(JsonFeedbackInfo.keys())
                channelslist = list(JsonFeedbackInfo.values())
                # return render_template('editVehicle.html', form=form) #DEBUGGUNG
            else:
                flash("Vehichle Update Failed - File: " +
                      configFilename + ", Error: " + str(error), 'info')
                return render_template('editVehicle.html', form=form)

        # Update vehicle for the app in the rfi.aops_api_vehicles table
        vehicle.groupname = request.form['groupname'].lower().split("_")[0]
        vehicle.location = request.form["location"]
        vehicle.owner_id = apiUser.id
        vehicle.frequencylist = frequencylist
        vehicle.channels = channelslist
        vehicle.configJSONFilename = configFilename
        vehicle.configJSON = configJSON
        vehicle.date_updated = datetime.datetime.now()
        vehicle.edit_notes = request.form["notes"]

        if form.validate_on_submit():
            db.session.merge(vehicle)
            db.session.commit()
            flash("Updated Vehicle: " + vehicle.vehiclename + ", Group: " +
                  vehicle.groupname + ", File: " + configFilename, 'info')

        vehicle2 = Registered_Vehicle.query.filter(
            Registered_Vehicle.id == vehicleID).first()

        return redirect(url_for('index'))

    return render_template('editVehicle.html', form=form)

# ------------------------------------------------------------------------------------------------------------------------------------------------
# Caclulate Occupency Percentage route
# =============================
#   * This route will allow SOPS API users to obtain a JSON message with the calculated OCC percentage for the 900 and 2400 frequencies of each 
#     mission manager EMP node of the CERTAIN1 and CERTAIN2 ranges.
#
# Extra Decorators:
#   * login_required
#
# Allowed HTTP Methods:
#   * GET
#
# URL Inputs:
#   * vehiclename
#   * rangename
#
# Returns:
#   * Redirect to index route upon successful app registration
# ------------------------------------------------------------------------------------------------------------------------------------------------

@app.route("/RFI/{}/calc-occ-percent/<string:vehiclename>/<string:rangename>".format(sdsp_version), methods=["GET"])
@token_required
def calcOCCpercent(vehiclename, rangename):
    HOST = 'localhost'
    PORT = 1883
    TOPICS = ['RFEnvironmentScan/900MHz/Node1', 
              'RFEnvironmentScan/900MHz/Node2', 
              'RFEnvironmentScan/900MHz/Node3',
              'RFEnvironmentScan/900MHz/Node4',
              'RFEnvironmentScan/900MHz/Node5',
              'RFEnvironmentScan/2400MHz/Node1', 
              'RFEnvironmentScan/2400MHz/Node2', 
              'RFEnvironmentScan/2400MHz/Node3',
              'RFEnvironmentScan/2400MHz/Node4',
              'RFEnvironmentScan/2400MHz/Node5']
    
    USERNAME = 'subscriber'
    PASSWORD = 'subscriber'
    RANGES = ['certain1', 'certain2']
    MESSAGES = []

    vehicleName = vehiclename.lower()
    range_name = rangename.lower()
  
    # check if range name exists, if not set to default
    if range_name not in RANGES:
        range_name = 'certain2'

    vehicle = Registered_Vehicle.query.filter(
        Registered_Vehicle.vehiclename == vehicleName).first()
    
    if vehicle:
        vehicleFrequInfo = vehicle.configJSON['channelFrequencyInfo']

        for topic in TOPICS:
            msg = subscribe.simple(topic, qos=0, hostname=HOST,
                                port=PORT, auth={'username': USERNAME, 'password': PASSWORD})
            # print("%s" % (msg.topic))
            MESSAGES.append(msg)
       
        # calculate OCC
        OCC_JSON1, OCC_JSON2 = CalculateOCCPercent_EMP(MESSAGES, vehicleFrequInfo)
        
        # Getting the current date and time
        dt = datetime.datetime.now()

        # getting the timestamp
        timestamp = datetime.datetime.timestamp(dt)

        OCC_JSON1["range"] = range_name
        OCC_JSON1["vehicleName"] = vehicleName
        OCC_JSON1["timestamp"] = timestamp

        OCC_JSON2["range"] = range_name
        OCC_JSON2["vehicleName"] = vehicleName
        OCC_JSON2["timestamp"] = timestamp

        if range_name == 'certain1':
            response = jsonify({'Spectrum_Occupency_Percent Certain': OCC_JSON1})
            response.status_code = 200

        else:
            response = jsonify({"Spectrum_Occupency_Percent": OCC_JSON2})
            response.status_code = 200

    else:
        message = "No vehicle with the name of '{}' could be found.".format(
            vehicleName)
        response = jsonify({'message': message})
        response.status_code = 404

    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# Caclulate TimeSpan Occupency Percentage route
# =============================
#   * This route will allow SOPS API users to obtain a JSON message with the calculated OCC percentage for the 900 and 2400 frequencies of each 
#     mission manager EMP node over a start and end time of a specified mission.
#
# Extra Decorators:
#   * login_required
#
# Allowed HTTP Methods:
#   * GET
#
# URL Inputs:
#   * mission_name
#   * start_time
#   * end_time
#
# Returns:
#   * Redirect to index route upon successful app registration
# ------------------------------------------------------------------------------------------------------------------------------------------------

@app.route("/RFI/{}/mission-manager-timespan-occ-percent/<string:mission_name>/<string:start_time>/<string:end_time>".format(sdsp_version), methods=["GET"])
@token_required
def calcTimeSpanOCCpercent(mission_name, start_time, end_time):
    '''
        This function will query the missiion manager database between a start anf end timestamp given the mission name.
        It will then calcualte the OCC percent on the scan values collected over those dates and return a JSON that contains 
        the calculation and scan metadata.  
    '''
    #authentication
    user = 'rfiservice'
    pw = 'sWsRFI@LaRC23'

    # capture and convert starting time
    converted_start_time = convert_time(start_time)
    converted_start_time_urlencode = urllib.parse.quote(converted_start_time).replace("%253A", "%3A")
    # print(converted_start_time_urlencode)

    # capture and convert ending time
    converted_end_time = convert_time(end_time)
    converted_end_time_urlencode = urllib.parse.quote(converted_end_time).replace("%253A", "%3A")
    # print(converted_end_time_urlencode)

    # Mission infromation by mission name Query - GOOD
    mission_info_url = 'http://dewey.larc.nasa.gov/api/missions/mission/?q=%7B"name"%3A"' + mission_name + '"%7D'
    mission_info_response = http_request(mission_info_url, user, pw)
    
    if mission_info_response.status_code == 200:
        mission_info_response_data = mission_info_response.json()
        mission_id = mission_info_response_data[0]['id']

        # Time range Sweep Scan Query - GOOD
        sweep_scan_url = 'http://dewey.larc.nasa.gov/api/sweep/sweepdata'
        sweep_url_ext = '/?q=%7B"mission"%3A' + str(mission_id) + '%2C"timestamp__gte"%3A"' + converted_start_time_urlencode + '"%2C"timestamp__lte"%3A"' + converted_end_time_urlencode + '"%7D&ordering=timestamp'
        sweep_scan_response = http_request(sweep_scan_url + sweep_url_ext, user, pw)
        
        if sweep_scan_response.status_code == 200:
            sweep_scan_response_data = sweep_scan_response.json()
            # parse response and calculate
            TIMESPAN_JSON = handel_time_sweep_scan_event(sweep_scan_response_data, mission_name, start_time, end_time)
            
            response = jsonify({'TimeSpan_Occupency_Percent': TIMESPAN_JSON})
            response.status_code = 200
        else:
            message = "Sweep scan error over start time '{}', and end time '{}'.".format(start_time, end_time)
            response = jsonify({'message': message})
            response.status_code = 404
    else:
        message = "No mission with the name of '{}' could be found.".format(mission_name)
        response = jsonify({'message': message})
        response.status_code = 404

    return response


# =============================
#   * The main route of the admin console
#   * Serves the "adminConsole.html" template where admins can view/edit registered sdsps and take action on app permission requests
#
# Extra Decorators:
#   * login_required
#   * admin_required
#
# Allowed HTTP Methods:
#   * GET
#
# URL Inputs:
#   * None
#
# Returns:
#   * None
# ------------------------------------------------------------------------------------------------------------------------------------------------
@app.route("/RFI/{}/admin-console".format(sdsp_version), methods=["GET"])
@login_required
@admin_required
def adminConsole():
    # Get list of registered sdsps to be displayed in the table
    # sdsps = [(s.id, s.name, s.version, s.ip_address, s.domain_name, s.date_added, s.status) for s in Registered_SDSP.query.order_by('name', 'version')]

    # # Get list of app permission requests to be displayed in a table if they exist
    # permReqAppIDs = [(p.id, p.app_id) for p in Requested_App_Permissions.query.filter_by(status='in progress')]
    # appReqs = []
    # for tup in permReqAppIDs:

    #     # Attach the associated requesting app with the permission request
    #     appReq = Registered_App.query.filter_by(id=tup[1]).first()
    #     appReqs.append((tup[0], appReq.name, appReq.version))

    # # Get a list of registered app permissions
    # appPermissions = []
    # regApps = Registered_App_Permissions.query.all()
    # for perm in regApps:
    #     app = Registered_App.query.filter_by(id=perm.app_id).first()
    #     sdsp = Registered_SDSP.query.filter_by(id=perm.sdsp_id).first()
    #     app_owner_email = API_User.query.filter_by(id=app.owner_id).first().email
    #     appPermissions.append((perm.id, app.name, app.version, app_owner_email, sdsp.name, sdsp.version, perm.allowed_methods, perm.date_granted))

    return render_template('adminConsole.html')
    # return render_template('adminConsole.html', sdsps=sdsps, permRequests=appReqs, appPerms=appPermissions)

# ------------------------------------------------------------------------------------------------------------------------------------------------
# API User registration route
# =============================
#   * Serves the "resetpwd.html" template with a "ResetPasswordForm" object
#   * Once the form has been successfully validated, a new password for API User object is created and committed to the "auth.api_user" table
#   * The user must request admin confirm password change
#
# Extra Decorators:
#   * None
#
# Allowed HTTP Methods:
#   * GET
#   * POST
#
# URL Inputs:
#   * None
#
# Returns:
#   * Redirect to index page
# ------------------------------------------------------------------------------------------------------------------------------------------------
# @app.route("/RFI/V1/{}/resetpwd".format(sdsp_version), methods=["GET", "POST"])
# # @admin_required
# def resetpwd():
#     form = ResetPasswordForm()

#     currentUser = AOPS_API_User.query.filter_by(email=form.email.data).first()

#     # print(currentUser)
#     if currentUser:

#         # Use BCRYPT to generate a password hash from the password form data. Hash is converted to a string to be stored in the table
#         passHash = bcrypt.generate_password_hash(form.password.data).decode('UTF-8')

#         # A new password is committed to the database under user
#         currentUser.passHash = passHash
#         currentUser.passReset = True
#         db.session.commit()

#         # Redirect to the index page. Flash a success message to the user
#         flash('The password was successfully reset. Account is locked awaiting administrator confirmation.', 'success')
#         return redirect(url_for('login'))

#     return render_template('resetpwd.html', form=form)


# =========================== WinProp Routes ================================================================================
# ----------------------------------------------------------------------
# Get the DbM values for a flightplan
# Jira Task SWSGND-793

@app.route("/RFI/V1/freq926_WinProp.flightplanLevels", methods=["POST"])
@token_required
def getfreq926WinPropFlightplanLevels():

    # Gather the flightplan data from the POST request
    flightplan = request.get_json().get('data')

    # Create a list of all the distinct altitudes in the database
    available_altitudes = [int(c.altitude[:-1]) for c
                           in Freq926_WinProp.query.distinct(
        Freq926_WinProp.altitude)]

    contours = dict()
    known_closest_altitudes = dict()
    output = []

    for i in range(len(flightplan) - 1):
        this_waypoint = flightplan[i]
        next_waypoint = flightplan[i+1]

        points_to_measure = [this_waypoint]
        points_to_measure += calculate_intermediate_pts(
            this_waypoint, next_waypoint)

        # Add the last waypoint to be processed during the final loop
        if i == len(flightplan) - 2:
            points_to_measure.append(next_waypoint)

        # Calculate the DbM value for each point
        for point in points_to_measure:
            point_lat = round(point.get('latitude'), 5)
            point_lon = round(point.get('longitude'), 5)
            point_alt = round(point.get('altitude'), 5)

            closest_alt = find_closest_alt(
                point_alt, available_altitudes, known_closest_altitudes)

            if closest_alt not in contours:
                # Gather contour data from the database at the altitude closest to the current point
                contours[closest_alt] = [
                    {
                        'level': c.level,
                        'polygons': [mplPath.Path(np.array(coordinate_list)) for coordinate_list
                                     in c.contour_list.get('coordinates')]
                    } for c in Freq926_WinProp.query.filter(
                        Freq926_WinProp.altitude == '{}m'.format(closest_alt))
                ]
                contours[closest_alt].sort(
                    key=lambda x: x['level'], reverse=True)

            point_level = find_dbm_level(
                contours, closest_alt, (point_lon, point_lat))

            output.append({
                'latitude': point_lat,
                'longitude': point_lon,
                'altitude': point_alt,
                'level': point_level
            })

    if len(output) > 0:
        response = jsonify({
            "freq926_Winprop_flightplan": output
        })
        response.status_code = 200
    else:
        message = "No records could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response

@app.route("/RFI/V1/Intrail_RFI", methods=["POST"])
@token_required
def getWinPropInPathRFI():
    # Payload should contain flight path coordinates (lat, long, alt) as well as time (eta)
    # Frequency, PIC Coordinates (coords for ground system pilot), and tx power frequency (frequency for ground station pilot)
    payload = request.get_json()

    filename = generate_unique_filename()
    read_winprop_filepath = os.getenv('READ_WINPROP_FILEPATH')
    winprop_run_log_filepath = os.getenv('WINPROP_RUN_LOG_FILEPATH')
    winprop_output_file = f"{read_winprop_filepath}{filename}.txt"
    winprop_output_run_log_file = f"{winprop_run_log_filepath}{filename}.log"
    external_sources_filepath = os.getenv('EXTERNAL_SOURCES_FILEPATH')
    write_payload_filepath = f"{os.getenv('WRITE_PAYLOAD_FOR_WINPROP_FILEPATH')}{filename}.json"

    # Boolean checks to ensure valid filepath is given and payload is not None, if false return 400 error
    # else try to process the request and catch any exceptions that occur.
    if not os.path.exists(read_winprop_filepath) or not os.path.exists(external_sources_filepath):
        message = f"One or more files do not exist at given path:\n {read_winprop_filepath}\n {external_sources_filepath}"
        response = jsonify({'message': message})
        print(message)
        response.status_code = 400

    elif not payload:
        message = "Error, payload must be included in the request."
        response = jsonify({'message': message})
        print(message)
        response.status_code = 400

    else:
        # Formatting payload from request to so winprop can be happy
        payload = add_external_sources_to_payload(
            "interfering_sources", payload, external_sources_filepath)

        parse_inpath_rfi_payload(payload, write_payload_filepath)

        with open(winprop_output_run_log_file, 'w') as f_obj:
            subprocess.run(
                ["/home/smartcity-larc/gateway/RFI/WinProp/output/APIExampleCPPFlightExample", write_payload_filepath, winprop_output_file], stdout=f_obj)

        for _ in range(1200):
            if not os.path.exists(winprop_output_file) and _ == 119:
                message = "request timed out after 120 seconds."
                response = jsonify({'message': message})
                response.status_code = 408
                return response
            elif not os.path.exists(winprop_output_file):
                sleep(1)
                continue
            elif os.path.exists(winprop_output_file):
                break

        # Formatting payload received from winprop so Frontend can be happy
        output_key = f"freq_{payload['comTransmitter']['freq(MHz)']}_inpath_rfi"
        output = marshal_inpath_rfi_data(winprop_output_file, output_key)
        output = parse_winprop_postprocess_file(output)
        output = calculate_intrail_rfi(output, output_key)

        # print(output)

        if len(output[output_key]) > 0:
            response = jsonify(output)
            # print(output)
            response.status_code = 200

        else:
            message = "In-path RFI was not calculated due to errors"
            response = jsonify({'message': message})
            response.status_code = 400

        # Clean up files created during endpoint call
        # Remove read and write files for WinProp
        os.remove(write_payload_filepath)
        os.remove(winprop_output_file)

        # Remove WinProp discard files
        dir = '/home/smartcity-larc/gateway/RFI/WinProp/output/discard'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
            
    return response


@app.route("/RFI/V1/Triangulate_Source", methods=["POST"])
# @token_required
def triangulateSource():
    payload = request.get_json()
    
    # These Environment Variables will need to be set prior to running the flask app
    crfs_ip = os.getenv('CRFS_IP')
    crfs_port = os.getenv('CRFS_PORT')
    crfs_triangulate_endpoint = os.getenv("CRFS_TRIANGULATE")
    crfs_user = os.getenv('CRFS_USERNAME')
    crfs_password = os.getenv('CRFS_PASSWORD')

    required_fields = ensure_fields(payload)
    crfs_url = f"https://{crfs_ip}:{crfs_port}{crfs_triangulate_endpoint}"

    if required_fields is False:
        message = "Error, payload must be included in the request."
        response = jsonify({'message': message})
        print(message)
        response.status_code = 400
    else:
        try:
            crfs_resp = requests.post(
                url=crfs_url, json=payload)
            response = jsonify(crfs_resp)
            response.status_code = 200
        except Exception as e:
            message = "Error, triangulating source" + crfs_resp
            response = jsonify({'message': message})
            print(e, crfs_resp)
            response.status_code = 400

    return response

# Historical Power Data
@app.route("/RFI/{}/mission_manager_historical_power/<string:timetype>/<string:weeknum>".format(sdsp_version), methods=["GET"])
@token_required
def getmissionmanagerhistoricalpower(timetype, weeknum):
    '''
    Description: Pull 2 weeks of max power for each CRFS node in hourly or daily format
    '''
    nodes = ['rfeye200340', 'rfeye200341', 'rfeye200342', 'rfeye200343', 'rfeye200474'] #'rfeye200474'
    Ttype = ['h', 'hourly','hour', 'd', 'daily', 'day']
    ttype = 'd'
    
    if timetype.lower() in Ttype:
        ttype = timetype.lower()

    weeknumber = int(weeknum)

    #cap weeks at 52, if 0 return 2 weeks
    if weeknumber > 52: 
        weeknumber = 52 
    elif weeknumber == 0: 
        weeknumber = 2

    plotting = False
    
    json_parameters = {'TimeZone': 'UTC', 'ConvertTimeZone': 'US/Eastern', 'TypeRequested': ttype, 'WeeksRequested': weeknumber}
    json_data_final = {'Historical_Power': [], 'Parameters':json_parameters}
    
    for node in nodes:
        json_data = {'node': None, 'data': None}
        json_format, retdata = calfunc(node, ttype, weeknumber)
        
        # convert json to dictionary
        if json_format:
            mm_historical_dict = json.loads(retdata)
        else:
            mm_historical_dict = retdata
        
        json_data['node'] = node
        json_data['data'] = mm_historical_dict
        json_data_final['Historical_Power'].append(json_data)

    if len(json_data_final) > 0:
        response = jsonify({'Mission_Manager_Historical_Data': json_data_final})
        response.status_code = 200
    else:
        message = "No records could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response