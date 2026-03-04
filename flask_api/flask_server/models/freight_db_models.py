from flask_server import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from uuid import uuid4
import jwt

db = SQLAlchemy()

#=========================== Authentication Tables =======================================================================

# This table will be watched by Debezium
class API_User(db.Model):
    __table_args__ = {"schema": "public"}
    __tablename__ = "api_user"
    
    
 
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column('email', db.String(120), unique=True, nullable=False)
    date_added = db.Column('date_added', db.DateTime())

    def __init__(self, name, email, date_added):
        self.name = name
        self.email = email
        self.date_added = datetime.now()

#=========================== Jobs Table =======================================================================

# # Materialize
# class Job_mv(db.Model):
#     __tablename__ = 'freight_jobs_mv' # Name of view in Materialize
#     __table_args__ = {'schema': 'public'} # If applicable

#     data = db.Column(JSONB, primary_key=True)

# PostgreSQL
class Job(db.Model):
    __table_args__ = {"schema": "public"}
    __tablename__ = "job"
 
    job_id = db.Column('job_id', db.Integer, primary_key=True)
    job_number = db.Column('job_number', db.String())
    origin = db.Column('origin', db.String())
    destination = db.Column('destination', db.String())
    client_name = db.Column('client_name', db.String())
    date_opened = db.Column('date_opened', db.String())

    # Virtual Property 1: Links to the JobHistory model
    jobHistory = db.relationship('JobHistory', back_populates='hisJob', cascade="all, delete-orphan")

    # Virtual Property 2: Links to a Shipment model
    shipment = db.relationship('Shipment', back_populates='shipping', cascade="all, delete-orphan")

    # Virtual Property 3: Links to a Invoice model
    invoice = db.relationship('Invoice', back_populates='bill', cascade="all, delete-orphan") 

    # Virtual Property 4: Links to a PurchaseOrder model
    purchseOrder = db.relationship('PurchaseOrder', back_populates='order', cascade="all, delete-orphan") 


    def __init__(self, job_id, job_number, origin, destination, client_name, date_opened):
        self.job_id = job_id
        self.job_number = job_number
        self.origin = origin
        self.destination = destination
        self.client_name = client_name
        self.date_opened = date_opened

#=========================== Jobs History Table =======================================================================

class JobHistory(db.Model):
    __table_args__ = {"schema": "public"}
    __tablename__ = "job_history"
 
    history_id = db.Column('history_id', db.Integer, primary_key=True)
    job_id = db.Column('job_id', db.Integer, db.ForeignKey(Job.job_id), nullable=False)
    status = db.Column('status', db.String())
    created_at = db.Column('created_at', db.String())

    # Virtual Property 1: Links to the Job model
    hisJob = db.relationship('Job', back_populates='jobHistory')

    def __init__(self, job_id, status, created_at):
        self.job_id = job_id
        self.status = status
        self.created_at = created_at


#=========================== Shipment Table =======================================================================

class Shipment(db.Model):
    __table_args__ = {"schema": "public"}
    __tablename__ = "shipment"
 
    record_id = db.Column('record_id', db.Integer, primary_key=True)
    shipment_id = db.Column('shipment_id', db.String(), unique=True, nullable=False)
    job_id = db.Column('job_id', db.Integer, db.ForeignKey(Job.job_id), nullable=False)
    mode = db.Column('mode', db.String())
    eta = db.Column('eta', db.String())

    # Virtual Property 1: Links to a Job model
    shipping = db.relationship('Job', back_populates='shipment')

    # Virtual Property 2: Links to a Freight model
    freight = db.relationship('Freight', back_populates='package', cascade="all, delete-orphan") 

    def __init__(self, shipment_id, job_id, mode, eta):
        self.shipment_id = shipment_id
        self.job_id = job_id
        self.mode = mode
        self.eta = eta


#=========================== Freight Table =======================================================================

class Freight(db.Model):
    __table_args__ = {"schema": "public"}
    __tablename__ = "freight"
 
    freight_id = db.Column('freight_id', db.String(), primary_key=True)
    shipment_id = db.Column('shipment_id', db.String(), db.ForeignKey(Shipment.shipment_id), nullable=False)
    description = db.Column('description', db.String())
    weight_kg = db.Column('weight_kg', db.Integer())
    volume_cbm = db.Column('volume_cbm', db.Float())
    quantity = db.Column('quantity', db.String())

    # Virtual Property 1: Links to a Shipment model
    package = db.relationship('Shipment', back_populates='freight') 

    def __init__(self, freight_id, shipment_id, description, weight_kg, volume_cbm, quantity):
        self.freight_id = freight_id
        self.shipment_id = shipment_id
        self.description = description
        self.weight_kg = weight_kg
        self.volume_cbm = volume_cbm
        self.quantity = quantity

#=========================== Invoice Table =======================================================================

class Invoice(db.Model):
    __table_args__ = {"schema": "public"}
    __tablename__ = "invoice"
 
    invoice_id = db.Column('invoice_id', db.String(), primary_key=True)
    job_id = db.Column('job_id', db.Integer, db.ForeignKey(Job.job_id), nullable=False)
    total_amount = db.Column('total_amount', db.Float())
    currency = db.Column('currency', db.String())
    due_date = db.Column('due_date', db.String())
    status = db.Column('status', db.String())

    # Virtual Property 1: Links to a Job model
    bill = db.relationship('Job', back_populates='invoice') 

    def __init__(self, invoice_id, job_id, total_amount, currency, due_date, status):
        self.invoice_id = invoice_id
        self.job_id = job_id
        self.total_amount = total_amount
        self.currency = currency
        self.due_date = due_date
        self.status = status

#=========================== Purchase Order Table =======================================================================

class PurchaseOrder(db.Model):
    __table_args__ = {"schema": "public"}
    __tablename__ = "purchaseorder"
 
    po_id = db.Column('po_id', db.Integer(), primary_key=True)
    job_id = db.Column('job_id', db.Integer, db.ForeignKey(Job.job_id), nullable=False)
    vendor_name = db.Column('vendor_name', db.String())
    amount_due_usd = db.Column('amount_due_usd', db.Float())
    service_type = db.Column('service_type', db.String())

    # Virtual Property 4: Links to a PurchseOrder model
    order = db.relationship('Job', back_populates='purchseOrder') 

    def __init__(self, po_id, job_id, vendor_name, amount_due_usd, service_type):
        self.po_id = po_id
        self.job_id = job_id
        self.vendor_name = vendor_name
        self.amount_due_usd = amount_due_usd
        self.service_type = service_type


