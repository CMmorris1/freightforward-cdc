from flask import flash, render_template, url_for, redirect, jsonify, request, session
from flask_server.models.freight_db_models import *
from flask_server.forms import *
from flask_server import app
from flask_talisman import Talisman
from datetime import datetime
from itertools import groupby
import jwt

talisman = Talisman(app)

def check_missing_items(data, required_table_fields):
    # check if Json contains all required table columns
    missing = [field for field in required_table_fields if field not in data]

    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    else:
        return 0

# --- JOB CRUD ROUTES MATERIALIZE ---
# @app.route('/jobs', methods=['GET'])
# def get_jobs():
#     results = db.session.execute(db.select(Job_mv)).scalars().all()
    
#     # Convert to JSON for the response
#     return jsonify([{"job_id": r.job_id, "job_number": r.job_number} for r in results])

#     # Access internal JSON fields directly from the .data attribute
#     jobs_list = []
#     for row in results:
#         job_info = row.data  # This is already a Python dict
#         jobs_list.append({
#             "job_id": job_info.get("job_id"),
#             "job_number": job_info.get("job_number"),
#             "origin": job_info.get("origin"),
#             "destination": job_info.get("destination"),
#             "client_name": job_info.get("client_name"),
#             "date_opened": job_info.get("date_opened")
#     })

#     return jsonify(jobs_list)

#--- JOB CRUD ROUTES POSTGRES---

# CREATE JOB
@app.route('/create_job', methods=['POST'])
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

# READ ALL JOBS
@app.route('/jobs_all', methods=['GET'])
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

# READ ONE JOB
@app.route('/job=<job_id>', methods=['GET'])
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

    # @app.route('/delete_job=<job_id>', methods=['GET', 'POST'])
    # def delete_job(job_id):
    #     job = Job.query.get_or_404(job_id)

    #     try:
    #         db.session.delete(job) # Mark the object for deletion
    #         db.session.commit() # Commit the changes to the database
    #         message = "Job '{}' deleted successfully!".format(job_id)
    #         response = jsonify({'message': message})
        
    #     except:
    #         db.session.rollback()
    #         message = "An error occured during the deletion of Job '{}'".format(job_id)
    #         response = jsonify({'message': message})
            
    #     return response

#--- JOB HISTORY CRUD ROUTES POSTGRES---

# CREATE JOB HISTORY
@app.route('/create_jobhistory', methods=['POST'])
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

# READ ALL JOBS HISTORIES
@app.route('/jobs_history_all', methods=['GET'])
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

# READ ONE JOB HISTORY
@app.route('/job_history=<job_id>', methods=['GET'])
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

#--- SHIPMENT CRUD ROUTES POSTGRES---

# READ ALL SHIPMENTS
@app.route('/shipments_all', methods=['GET'])
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

# READ ONE SHIPMENT
@app.route('/shipment=<shipment_id>', methods=['GET'])
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


#--- FREIGHT CRUD ROUTES POSTGRES---

# READ ALL FREIGHTS
@app.route('/freights_all', methods=['GET'])
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

# READ ONE FREIGHT
@app.route('/freight=<freight_id>', methods=['GET'])
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

#--- INVOICE CRUD ROUTES POSTGRES---


# READ ALL INVOICES
@app.route('/invoices_all', methods=['GET'])
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

# READ ONE INVOICE
@app.route('/invoice=<invoice_id>', methods=['GET'])
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


#--- PURCHASE ORDER CRUD ROUTES POSTGRES---

# READ ALL PURCHASE ORDERS
@app.route('/purchaseorders_all', methods=['GET'])
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


# READ ONE PURCHASE ORDER
@app.route('/purchaseorder=<job_id>', methods=['GET'])
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

# # CREATE
# @app.route('/books', methods=['POST'])
# def create_book():
#     if not request.json or not 'title' in request.json or not 'author' in request.json:
#         abort(400) # Bad request if data is missing
    
#     new_book = Book(
#         title=request.json['title'],
#         author=request.json['author']
#     )
#     db.session.add(new_book)
#     db.session.commit() # Commit the session to save the new instance
#     return jsonify({'book': new_book.to_dict()}), 201

# # READ all
# @app.route('/books', methods=['GET'])
# def get_books():
#     books = Book.query.all() # Fetch all Book items
#     return jsonify([book.to_dict() for book in books])

# # READ one
# @app.route('/books/<int:book_id>', methods=['GET'])
# def get_book(book_id):
#     book = Book.query.get_or_404(book_id) # Fetch a specific item by ID
#     return jsonify(book.to_dict())

# # UPDATE
# @app.route('/books/<int:book_id>', methods=['PUT'])
# def update_book(book_id):
#     book = Book.query.get_or_404(book_id)
#     if not request.json:
#         abort(400)
    
#     # Update the book object with new data
#     book.title = request.json.get('title', book.title)
#     book.author = request.json.get('author', book.author)
    
#     db.session.commit() # Commit the changes to the database
#     return jsonify({'book': book.to_dict()})

# # DELETE
# @app.route('/books/<int:book_id>', methods=['DELETE'])
# def delete_book(book_id):
#     book = Book.query.get_or_404(book_id)
#     db.session.delete(book) # Mark the object for deletion
#     db.session.commit() # Finalize the deletion
#     return jsonify({'result': True, 'message': 'Book deleted'})