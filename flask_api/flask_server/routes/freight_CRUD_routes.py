from flask import flash, render_template, url_for, redirect, jsonify, request, session
from flask_server.models.freight_db_models import *
from flask_server.forms import *
from flask_server import app
from flask_talisman import Talisman
from datetime import datetime
from itertools import groupby
import jwt

talisman = Talisman(app)

# check if Json contains all required table columns
def check_missing_items(data, required_table_fields):
    
    missing = [field for field in required_table_fields if field not in data]

    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    else:
        return 0

# =========================== JOB TABLE CRUD Routes ===================================================

#------------------------------------------------------------------------------------------------------------------------------------------------
# CREATE JOB
#=============================
#   Creates a new Job in the freightJobs database 'job' table 
#
# URL Inputs:
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * POST
#
# Returns: 
#   * 400 - Failed
#   * 201 - Created
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/job/create', methods=['POST'])
def create_job():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    table_fields = ['job_id', 'job_number', 'origin', 'destination', 'client_name', 'date_opened']

    check = check_missing_items(data, table_fields)
    
    if check == 0:
        new_job = Job(
            job_id = request.json['job_id'],
            job_number = request.json['job_number'],
            origin = request.json['origin'],
            destination = request.json['destination'],
            client_name = request.json['client_name'],
            date_opened = request.json['date_opened']
        )

        db.session.add(new_job)
        db.session.commit() 

        return jsonify({"message": "Job created", "job_id": new_job.job_id}), 201
    else:
        return check

#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ALL JOBS
#=============================
#   Reads all current Jobs from the freightJobs database 'job' table 
#
# URL Inputs:
#   * None
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/jobs', methods=['GET'])
def get_jobs_all():
    # Query the job table and build a list of dictionaries for all relavent entries
    Jobs_dict = [{
        "job_id": c.job_id,
        "job_number": c.job_number,
        "origin": c.origin,
        "destination": c.destination,
        "client_name": c.client_name,
        "date_opened": c.date_opened
    } for c in Job.query.all()]

    if len(Jobs_dict) > 0:
        response = jsonify({'Jobs_All': Jobs_dict})
        response.status_code = 200
    else:
        message = "No jobs could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response

#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ONE JOB
#=============================
#   Reads one  Job from the freightJobs database 'job' table 
#
# URL Inputs:
#   * job_id
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/job/<job_id>', methods=['GET'])
def get_job(job_id):
    # Query the job table and filter specifc job id
    Job_dict = [{
        "job_id": c.job_id,
        "job_number": c.job_number,
        "origin": c.origin,
        "destination": c.destination,
        "client_name": c.client_name,
        "date_opened": c.date_opened
    } for c in Job.query.filter_by(job_id=job_id).all()]

    if len(Job_dict) > 0:
        response = jsonify({'Job': Job_dict})
        response.status_code = 200
    else:
        message = "No job with ID of '{}' could be found.".format(job_id)
        response = jsonify({'message': message})
        response.status_code = 400

    return response

#------------------------------------------------------------------------------------------------------------------------------------------------
# UPDATE JOB
#=============================
#   Upadates one Job from the freightJobs database 'job' table 
#
# URL Inputs:
#   * job_id
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * PUT
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/job/update/<job_id>', methods=['PUT'])
def update_job(job_id):
    job = Job.query.filter_by(job_id=job_id).first_or_404()
    
    json_data = request.get_json()

    if not request.json:
        abort(400)

    # Update the job object with new data
    if json_data is not None and 'job_number' in json_data:
        job.job_number = request.json.get('job_number', job.job_number)
    if json_data is not None and 'origin' in json_data:
        job.origin = request.json.get('origin', job.origin)
    if json_data is not None and 'destination' in json_data:
        job.destination = request.json.get('destination', job.destination)
    if json_data is not None and 'client_name' in json_data:
        job.client_name = request.json.get('client_name', job.client_name)
    if json_data is not None and 'date_opened' in json_data:
        job.date_opened = request.json.get('date_opened', job.date_opened)
    
    db.session.commit() # Commit the changes to the database

    return jsonify({"message": "Job updated", "job_id": job.job_id})


#------------------------------------------------------------------------------------------------------------------------------------------------
# DELETE JOB
#=============================
#   Deletes one Job from the freightJobs database 'job' table 
#
# URL Inputs:
#   * job_id
#
# Allowed HTTP Methods: 
#   * DELETE
#
# Tables Affected:
#   * Variable: job_id
#   * Tables:
#       - JobHistory
#       - Shipment
#       - Invoice
#       - PurchaseOrder
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/job/delete/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    job = Job.query.filter_by(job_id=job_id).first_or_404()
    db.session.delete(job) 
    db.session.commit()
    return jsonify({'Result': True, 'message': 'Job Deleted'})


# =========================== JOB HISTORY TABLE CRUD Routes ===================================================

#------------------------------------------------------------------------------------------------------------------------------------------------
# CREATE JOB HISTORY
#=============================
#   Creates a new Job History in the freightJobs database 'job_history' table 
#
# URL Inputs:
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * POST
#
# Returns: 
#   * 400 - Failed
#   * 201 - Created
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/job_history/create', methods=['POST'])
def create_jobhistory():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    table_fields = ['job_id', 'status', 'created_at']

    check = check_missing_items(data, table_fields)
    
    if check == 0:
        new_jobHistory = JobHistory(
            job_id = request.json['job_id'],
            status = request.json['status'],
            created_at = request.json['created_at']
        )
        print(new_jobHistory)
        db.session.add(new_jobHistory)
        db.session.commit() 

        return jsonify({"message": "Job History created", "job_id": new_jobHistory.job_id}), 201
    else:
        return check

#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ALL JOB HISTORIES
#=============================
#   Reads all current Job Histories from the freightJobs database 'job_history' table 
#
# URL Inputs:
#   * None
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/jobs_history', methods=['GET'])
def get_jobs_history_all():
    # Query the job_history table and build a list of dictionaries for all relavent entries
    Jobs_history_dict = [{
        "history_id": c.history_id,
        "job_id": c.job_id,
        "status": c.status,
        "created_at": c.created_at
    } for c in JobHistory.query.all()]

    if len(Jobs_history_dict) > 0:
        response = jsonify({'Job_History_All': Jobs_history_dict})
        response.status_code = 200
    else:
        message = "No jobs history could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response
#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ONE JOB HISTORY
#=============================
#   Reads one Job History from the freightJobs database 'job_history' table 
#
# URL Inputs:
#   * job_id
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/job_history/<job_id>', methods=['GET'])
def get_job_history(job_id):
    # Query the job table and filter specifc job id
    Job_history_dict = [{
        "history_id": c.history_id,
        "job_id": c.job_id,
        "status": c.status,
        "created_at": c.created_at
    } for c in JobHistory.query.filter_by(job_id=job_id).all()]

    if len(Job_history_dict) > 0:
        response = jsonify({'Job_History': Job_history_dict})
        response.status_code = 200
    else:
        message = "No job history for job ID of '{}' could be found.".format(job_id)
        response = jsonify({'message': message})
        response.status_code = 400

    return response

#------------------------------------------------------------------------------------------------------------------------------------------------
# UPDATE JOB HISTORY
#=============================
#   Upadates one Job History from the freightJobs database 'job_history' table 
#
# URL Inputs:
#   * job_id
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * PUT
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/job_history/update/<job_id>', methods=['PUT'])
def update_job_histroy(job_id):
   
    job_histroy = JobHistory.query.filter_by(job_id=job_id).first_or_404()
    
    json_data = request.get_json()

    if not request.json:
        abort(400)

    # Update the job history object with new data
    if json_data is not None and 'status' in json_data:
        job_histroy.status = request.json.get('status', job_histroy.status)
    if json_data is not None and 'created_at' in json_data:
        job_histroy.created_at = request.json.get('created_at', job_histroy.created_at)
    
    db.session.commit() # Commit the changes to the database

    return jsonify({"message": "Job History updated", "job_id": job_histroy.job_id})

#------------------------------------------------------------------------------------------------------------------------------------------------
# DELETE JOB HISTROY
#=============================
#   Deletes one Job History from the freightJobs database 'job_history' table 
#
# URL Inputs:
#   * job_id
#
# Allowed HTTP Methods: 
#   * DELETE
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/job_history/delete/<job_id>', methods=['DELETE'])
def delete_jobs_history(job_id):
    job_history = JobHistory.query.filter_by(job_id=job_id).delete() # DELETES all records with filter condition
    db.session.commit()
    return jsonify({'Result': True, 'message': 'Job Deleted'})



# =========================== SHIPMENT TABLE CRUD Routes ===================================================

#------------------------------------------------------------------------------------------------------------------------------------------------
# CREATE SHIPMENT
#=============================
#   Creates a new Shipment in the freightJobs database 'shipment' table 
#
# URL Inputs:
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * POST
#
# Returns: 
#   * 400 - Failed
#   * 201 - Created
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/shipment/create', methods=['POST'])
def create_shipment():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    table_fields = ['shipment_id', 'job_id', 'mode', 'eta']

    check = check_missing_items(data, table_fields)
    
    if check == 0:
        new_shipment = Shipment(
            shipment_id = request.json['shipment_id'],
            job_id = request.json['job_id'],
            mode = request.json['mode'],
            eta = request.json['eta']
        )

        db.session.add(new_shipment)
        db.session.commit() 

        return jsonify({"message": "Shipment created", "job_id": new_shipment.shipment_id}), 201
    else:
        return check

#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ALL SHIPMENTS
#=============================
#   Reads all Shipments from the freightJobs database 'shipment' table 
#
# URL Inputs:
#   * None
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/shipments', methods=['GET'])
def get_shipments_all():
    # Query the shipment table and build a list of dictionaries for all relavent entries
    Shipments_dict = [{
        "record_id": c.record_id,
        "shipment_id": c.shipment_id,
        "job_id": c.job_id,
        "mode": c.mode,
        "eta": c.eta
    } for c in Shipment.query.all()]

    if len(Shipments_dict) > 0:
        response = jsonify({'Shipments_All': Shipments_dict})
        response.status_code = 200
    else:
        message = "No shipments could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response

#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ONE SHIPMENT
#=============================
#   Reads one shipment from the freightJobs database 'shipment' table 
#
# URL Inputs:
#   * shipment_id
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/shipment/<shipment_id>', methods=['GET'])
def get_shipment(shipment_id):
    # Query the shipment table and filter specifc shipment id
    Shipment_dict = [{
        "record_id": c.record_id,
        "shipment_id": c.shipment_id,
        "job_id": c.job_id,
        "mode": c.mode,
        "eta": c.eta
    } for c in Shipment.query.filter_by(shipment_id=shipment_id).all()]

    if len(Shipment_dict) > 0:
        response = jsonify({'Shipment': Shipment_dict})
        response.status_code = 200
    else:
        message = "No Shipment with ID of '{}' could be found.".format(shipment_id)
        response = jsonify({'message': message})
        response.status_code = 400

    return response


#------------------------------------------------------------------------------------------------------------------------------------------------
# UPDATE SHIPMENT
#=============================
#   Upadates one Shipment from the freightJobs database 'shipment' table 
#
# URL Inputs:
#   * job_id
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * PUT
#
# Tables Affected:
#   * Variable: shipment_id
#   * Tables:
#       - Freight
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/shipment/update/<job_id>', methods=['PUT'])
def update_shipment(job_id):
   
    shipment = Shipment.query.filter_by(job_id=job_id).first_or_404()
    
    json_data = request.get_json()

    if not request.json:
        abort(400)

    # Update the shipment object with new data
    if json_data is not None and 'mode' in json_data:
        shipment.mode = request.json.get('mode', shipment.mode)
    if json_data is not None and 'eta' in json_data:
        shipment.eta = request.json.get('eta', shipment.eta)
    
    db.session.commit() # Commit the changes to the database

    return jsonify({"message": "Shipment updated", "job_id": shipment.job_id})

#------------------------------------------------------------------------------------------------------------------------------------------------
# DELETE SHIPMENT
#=============================
#   Deletes one Shipment from the freightJobs database 'shipment' table 
#
# URL Inputs:
#   * job_id
#
# Allowed HTTP Methods: 
#   * DELETE
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/shipment/delete/<job_id>', methods=['DELETE'])
def delete_shipment(job_id):
    shipment = Shipment.query.filter_by(job_id=job_id).first_or_404()
    db.session.delete(shipment) 
    db.session.commit()
    return jsonify({'Result': True, 'message': 'Shipment Deleted'})


# =========================== FREIGHT TABLE CRUD Routes ===================================================

#------------------------------------------------------------------------------------------------------------------------------------------------
# CREATE FREIGHT
#=============================
#   Creates a new Freight in the freightJobs database 'freight' table 
#
# URL Inputs:
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * POST
#
# Returns: 
#   * 400 - Failed
#   * 201 - Created
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/freight/create', methods=['POST'])
def create_freight():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    table_fields = ['freight_id', 'shipment_id', 'description', 'weight_kg', 'volume_cbm', 'quantity']

    check = check_missing_items(data, table_fields)
    
    if check == 0:
        new_freight = Freight(
            freight_id = request.json['freight_id'],
            shipment_id = request.json['shipment_id'],
            description = request.json['description'],
            weight_kg = request.json['weight_kg'],
            volume_cbm = request.json['volume_cbm'],
            quantity = request.json['quantity']
        )

        db.session.add(new_freight)
        db.session.commit() 

        return jsonify({"message": "Freight created", "freight_id": new_freight.freight_id}), 201
    else:
        return check

#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ALL FREIGHTS
#=============================
#   Reads all Freights from the freightJobs database 'freight' table 
#
# URL Inputs:
#   * None
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/freights', methods=['GET'])
def get_freights_all():
    # Query the freight table and build a list of dictionaries for all relavent entries
    Freights_dict = [{
        "freight_id": c.freight_id,
        "shipment_id": c.shipment_id,
        "description": c.description,
        "weight_kg": c.weight_kg,
        "volume_cbm": c.volume_cbm,
        "quantity": c.quantity
    } for c in Freight.query.all()]

    if len(Freights_dict) > 0:
        response = jsonify({'Freights_All': Freights_dict})
        response.status_code = 200
    else:
        message = "No freights could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response

#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ONE FREIGHT
#=============================
#   Reads one Freight from the freightJobs database 'freight' table 
#
# URL Inputs:
#   * freight_id
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/freight/<freight_id>', methods=['GET'])
def get_freight(freight_id):
    # Query the freight table and filter specifc shipment id
    Freight_dict = [{
        "freight_id": c.freight_id,
        "shipment_id": c.shipment_id,
        "description": c.description,
        "weight_kg": c.weight_kg,
        "volume_cbm": c.volume_cbm,
        "quantity": c.quantity
    } for c in Freight.query.filter_by(freight_id=freight_id).all()]

    if len(Freight_dict) > 0:
        response = jsonify({'Freight': Freight_dict})
        response.status_code = 200
    else:
        message = "No freight with ID of '{}' could be found.".format(freight_id)
        response = jsonify({'message': message})
        response.status_code = 400

    return response

#------------------------------------------------------------------------------------------------------------------------------------------------
# UPDATE FREIGHT
#=============================
#   Upadates one Freight from the freightJobs database 'freight' table 
#
# URL Inputs:
#   * job_id
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * PUT
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/freight/update/<freight_id>', methods=['PUT'])
def update_freight(freight_id):
   
    freight = Freight.query.filter_by(freight_id=freight_id).first_or_404()
    
    json_data = request.get_json()

    if not request.json:
        abort(400)

    # Update the freight object with new data
    if json_data is not None and 'description' in json_data:
        freight.description = request.json.get('description', freight.description)
    if json_data is not None and 'volume_cbm' in json_data:
        freight.volume_cbm = request.json.get('volume_cbm', freight.volume_cbm)
    if json_data is not None and 'weight_kg' in json_data:
        freight.weight_kg = request.json.get('weight_kg', freight.weight_kg)
    if json_data is not None and 'quantity' in json_data:
        freight.quantity = request.json.get('quantity', freight.quantity)

    db.session.commit() # Commit the changes to the database

    return jsonify({"message": "Freight updated", "freight_id": freight.freight_id})

#------------------------------------------------------------------------------------------------------------------------------------------------
# DELETE FREIGHT
#=============================
#   Deletes one Freight from the freightJobs database 'freight' table 
#
# URL Inputs:
#   * freight_id
#
# Allowed HTTP Methods: 
#   * DELETE
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/freight/delete/<freight_id>', methods=['DELETE'])
def delete_freight(freight_id):
    freight = Freight.query.filter_by(freight_id=freight_id).first_or_404()
    db.session.delete(freight) 
    db.session.commit()
    return jsonify({'Result': True, 'message': 'Freight Deleted'})


# =========================== INVOICE TABLE CRUD Routes ===================================================

#------------------------------------------------------------------------------------------------------------------------------------------------
# CREATE INVOICE
#=============================
#   Creates a new Invoice in the freightJobs database 'invoice' table 
#
# URL Inputs:
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * POST
#
# Returns: 
#   * 400 - Failed
#   * 201 - Created
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/invoice/create', methods=['POST'])
def create_invoice():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    table_fields = ['invoice_id', 'job_id', 'total_amount', 'currency', 'due_date', 'status']

    check = check_missing_items(data, table_fields)
    
    if check == 0:
        new_invoice = Invoice(
            invoice_id = request.json['invoice_id'],
            job_id = request.json['job_id'],
            total_amount = request.json['total_amount'],
            currency = request.json['currency'],
            due_date = request.json['due_date'],
            status = request.json['status']
        )

        db.session.add(new_invoice)
        db.session.commit() 

        return jsonify({"message": "Invoice created", "invoice_id": new_invoice.invoice_id}), 201
    else:
        return check

#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ALL INVOICES
#=============================
#   Reads all Invoices from the freightJobs database 'invocie' table 
#
# URL Inputs:
#   * None
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/invoices', methods=['GET'])
def get_invoices_all():
    # Query the freight table and build a list of dictionaries for all relavent entries
    Invoices_dict = [{
        "invoice_id": c.invoice_id,
        "job_id": c.job_id,
        "total_amount": c.total_amount,
        "currency": c.currency,
        "due_date": c.due_date,
        "status": c.status
    } for c in Invoice.query.all()]

    if len(Invoices_dict) > 0:
        response = jsonify({'Invoices_All': Invoices_dict})
        response.status_code = 200
    else:
        message = "No invoices could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response

#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ONE INVOICE
#=============================
#   Reads one Invoice from the freightJobs database 'invoice' table 
#
# URL Inputs:
#   * invoice_id
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/invoice/<invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    # Query the freight table and filter specifc shipment id
    Invoice_dict = [{
        "invoice_id": c.invoice_id,
        "job_id": c.job_id,
        "total_amount": c.total_amount,
        "currency": c.currency,
        "due_date": c.due_date,
        "status": c.status
    } for c in Invoice.query.filter_by(invoice_id=invoice_id).all()]

    if len(Invoice_dict) > 0:
        response = jsonify({'Invoice': Invoice_dict})
        response.status_code = 200
    else:
        message = "No invoice with ID of '{}' could be found.".format(invoice_id)
        response = jsonify({'message': message})
        response.status_code = 400

    return response

#------------------------------------------------------------------------------------------------------------------------------------------------
# UPDATE INVOICE
#=============================
#   Upadates one Invoice from the freightJobs database 'invoice' table 
#
# URL Inputs:
#   * job_id
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * PUT
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/invoice/update/<job_id>', methods=['PUT'])
def update_invoice(job_id):
   
    invoice = Invoice.query.filter_by(job_id=job_id).first_or_404()
    
    json_data = request.get_json()

    if not request.json:
        abort(400)

    # Update the invoice object with new data
    if json_data is not None and 'total_amount' in json_data:
        invoice.total_amount = request.json.get('total_amount', invoice.total_amount)
    if json_data is not None and 'currency' in json_data:
        invoice.currency = request.json.get('currency', invoice.currency)
    if json_data is not None and 'due_date' in json_data:
        invoice.due_date = request.json.get('due_date', invoice.due_date)
    if json_data is not None and 'status' in json_data:
        invoice.status = request.json.get('status', invoice.status)

    db.session.commit() # Commit the changes to the database

    return jsonify({"message": "Invoice updated", "job_id": invoice.job_id})


#------------------------------------------------------------------------------------------------------------------------------------------------
# DELETE INVOICE
#=============================
#   Deletes one Invoice from the freightJobs database 'invoice' table 
#
# URL Inputs:
#   * invoice_id
#
# Allowed HTTP Methods: 
#   * DELETE
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/invoice/delete/<invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    invoice = Invoice.query.filter_by(invoice_id=invoice_id).first_or_404()
    db.session.delete(invoice) 
    db.session.commit()
    return jsonify({'Result': True, 'message': 'Invoice Deleted'})


# =========================== PURCHASE ORDER TABLE CRUD Routes ===================================================

#------------------------------------------------------------------------------------------------------------------------------------------------
# CREATE PURCHASE ORDER
#=============================
#   Creates a new Purchase Order in the freightJobs database 'purchaseorder' table 
#
# URL Inputs:
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * POST
#
# Returns: 
#   * 400 - Failed
#   * 201 - Created
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/purchaseorder/create', methods=['POST'])
def create_purchaseorder():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    table_fields = ['po_id', 'job_id', 'vendor_name', 'amount_due_usd', 'service_type']

    check = check_missing_items(data, table_fields)
    
    if check == 0:
        new_purchaseorder = PurchaseOrder(
            po_id = request.json['po_id'],
            job_id = request.json['job_id'],
            vendor_name = request.json['vendor_name'],
            amount_due_usd = request.json['amount_due_usd'],
            service_type = request.json['service_type']
        )

        db.session.add(new_purchaseorder)
        db.session.commit() 

        return jsonify({"message": "Purchse Order created", "po_id": new_purchaseorder.po_id}), 201
    else:
        return check


#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ALL PURCHASE ORDERS
#=============================
#   Reads all Purchase Orders from the freightJobs database 'purchaseorder' table 
#
# URL Inputs:
#   * None
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/purchaseorders', methods=['GET'])
def get_purchaseorders_all():
    # Query the purchase order table and build a list of dictionaries for all relavent entries
    PurchaseOrders_dict = [{
        "po_id": c.po_id,
        "job_id": c.job_id,
        "vendor_name": c.vendor_name,
        "amount_due_usd": c.amount_due_usd,
        "service_type": c.service_type
    } for c in PurchaseOrder.query.all()]

    if len(PurchaseOrders_dict) > 0:
        response = jsonify({'Purchase_Orders_all': PurchaseOrders_dict})
        response.status_code = 200
    else:
        message = "No invoices could be found."
        response = jsonify({'message': message})
        response.status_code = 400

    return response


#------------------------------------------------------------------------------------------------------------------------------------------------
# READ ONE PURCHASE ORDERS
#=============================
#   Reads one Purchase Order from the freightJobs database 'purchaseorder' table 
#
# URL Inputs:
#   * job_id
#
# Allowed HTTP Methods: 
#   * GET
#
# Returns: 
#   * 400 - Failed
#   * 200 - Success
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/purchaseorder/<job_id>', methods=['GET'])
def get_purchaseorder(job_id):
    # Query the freight table and filter specifc shipment id
    PurchaseOrder_dict = [{
        "po_id": c.po_id,
        "job_id": c.job_id,
        "vendor_name": c.vendor_name,
        "amount_due_usd": c.amount_due_usd,
        "service_type": c.service_type
    } for c in PurchaseOrder.query.filter_by(job_id=job_id).all()]

    if len(PurchaseOrder_dict) > 0:
        response = jsonify({'Purchase_Order': PurchaseOrder_dict})
        response.status_code = 200
    else:
        message = "No purchase order with job ID of '{}' could be found.".format(job_id)
        response = jsonify({'message': message})
        response.status_code = 400

    return response

#------------------------------------------------------------------------------------------------------------------------------------------------
# UPDATE PURCHASE ORDER
#=============================
#   Upadates one Purchase Order from the freightJobs database 'purchaseorder' table 
#
# URL Inputs:
#   * job_id
#   * JSON Payload
#
# Allowed HTTP Methods: 
#   * PUT
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/purchaseorder/update/<job_id>', methods=['PUT'])
def update_purchaseorder(job_id):
   
    purchaseorder = PurchaseOrder.query.filter_by(job_id=job_id).first_or_404()
    
    json_data = request.get_json()

    if not request.json:
        abort(400)

    # Update the PurchaseOrder object with new data
    if json_data is not None and 'vendor_name' in json_data:
        purchaseorder.vendor_name = request.json.get('vendor_name', purchaseorder.vendor_name)
    if json_data is not None and 'amount_due_usd' in json_data:
        purchaseorder.amount_due_usd = request.json.get('amount_due_usd', purchaseorder.amount_due_usd)
    if json_data is not None and 'service_type' in json_data:
        purchaseorder.service_type = request.json.get('service_type', purchaseorder.service_type)

    db.session.commit() # Commit the changes to the database

    return jsonify({"message": "Purchase Order updated", "job_id": purchaseorder.job_id})

#------------------------------------------------------------------------------------------------------------------------------------------------
# DELETE PURCHASE ORDER
#=============================
#   Deletes one Purchase Order from the freightJobs database 'purchaseorder' table 
#
# URL Inputs:
#   * invoice_id
#
# Allowed HTTP Methods: 
#   * DELETE
#
# Returns: 
#   * JSON Success Message
#   * Failure Response
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/purchaseorder/delete/<job_id>', methods=['DELETE'])
def delete_purchaseorder(job_id):
    purchaseorder = PurchaseOrder.query.filter_by(job_id=job_id).first_or_404()
    db.session.delete(purchaseorder) 
    db.session.commit()
    return jsonify({'Result': True, 'message': 'PurchaseOrder Deleted'})

