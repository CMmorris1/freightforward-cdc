"""
Date: February 2026

Description: Postgres main to launch driver function for uploading data to database

Author: Christopher M. Morris

E-mail: cmorris.morris@gmail.com

Company: Self

Location: Freelance

Modified:
    
"""
import os
import sys
import json
import time
import psycopg2
import global_vars
import random
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import execute_values
from datetime import date, datetime, timedelta


def connectToPostgres_DB(dictionary):
    """ 
    This function will connect to the base postgres database. This database is installed by default when postgres is installed.
    Because all users should have this default databse, it will be used as a standard launch point for all other databases.

    After a successful connection is made to the postgres database, the logic calls a function to check if the desired database, referenced 
    within the input data dictionary, caan be found. If it is not found, the function creates the desird database.

    Parameters: Data Dictionary

    Returns: N/A
    """
    # Connect to the postgres database. 
    # If unable to connect, catch exception and display error. Exit upon failure 

    db_name = dictionary['database']['databaseName']
    db_user = dictionary['database']['user']
    db_password = dictionary['database']['password']
    db_host = dictionary['database']['host']
    db_port = dictionary['database']['port']

    try:
        connection = psycopg2.connect(database = 'postgres', user = db_user, password = db_password, host = db_host, port = db_port)
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    except psycopg2.OperationalError as e:
        print (global_vars.bcolors.FAIL + "CONNECTION ERROR: Could not connect to postgres server. Caught Exception: \n" + global_vars.bcolors.ENDC)
        print (e)
        exit()

    # Display if the connection was successful
    print(global_vars.bcolors.OKGREEN + "SUCCESS: Postgres Database Connection Successful. %s" % (global_vars.bcolors.ENDC))

    cursor = connection.cursor()

    # Check if desired database exists, create database if it doesn't exist
    check_and_create_DB(cursor, connection, db_name)

    connection.close()


def check_and_create_DB(cursor, connection, database):
    """ 
    This function will check if the database exists. If it does not exists it will create the databse

    Parameters: 
        cursor and connection - Links to the postgres database
        database - Desired database to be checked

    Returns: N/A
    """

    check_statement = "SELECT EXISTS ( SELECT datname FROM pg_catalog.pg_database WHERE lower(datname) = lower('%s'));" % database
   
    cursor.execute(check_statement)

    dbExists = cursor.fetchone()[0]                
    
    if not dbExists:
        print(global_vars.bcolors.INFO + "INFO: %s does not exist. Generating database... %s" % (database, global_vars.bcolors.INFO))
        create_statement = 'CREATE DATABASE ' + database + ';'
        cursor.execute(create_statement)
        print(global_vars.bcolors.OKGREEN + "SUCCESS: 'created database %s. Connecting to new database... %s" % (database, global_vars.bcolors.ENDC))
    

def connectTo_DB(dictionary):
    """ 
    This function will connect to the database referenced within the input data dictionary.

    Parameters:
        dictionary - This dictionary created from a .json file and contains databse name and table information

    Returns: cursor, connection - Connections to the desired database
    """
    # Connect to the database from input dictionary. 
    # If unable to connect, catch exception and display error. Exit upon failure 

    db_name = dictionary['database']['databaseName']
    db_user = dictionary['database']['user']
    db_password = dictionary['database']['password']
    db_host = dictionary['database']['host']
    db_port = dictionary['database']['port']

    # Connect to database
    try:
        connection = psycopg2.connect(database = db_name, user = db_user, password = db_password, host = db_host, port = db_port)
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    except psycopg2.OperationalError as e:
        print (global_vars.bcolors.FAIL + "CONNECTION ERROR: Could not connect to postgres server. Caught Exception: \n" + global_vars.bcolors.ENDC)
        print (e)
        exit()
    
    cursor = connection.cursor()

    # Display if the connection was successful
    # print(global_vars.bcolors.OKGREEN + "SUCCESS: %s Database Connection Successful.\n %s" % (db_name, global_vars.bcolors.ENDC))

    return cursor, connection


def check_and_build_tables_dynamically(cursor, connection, tablename, createTable):
    """ 
    This function will dynamically check and build a PostgreSQL table(s).
    
    Parameters: 
        cursor: postgres database cursor 
        connection: postgres database connection
        table_name: table to be checked or created 
        createTable: SQL CREATE TABLE string

    Returns: N/A

    """

    query = global_vars.tableExists_query

    # query for table name
    cursor.execute(query, [tablename])

    check = cursor.fetchone()[0]

    if not check:
        print(global_vars.bcolors.WARNING + "WARNING: " + str(tablename) + " table does not exist. Creating table..." + global_vars.bcolors.ENDC)
        
        try:
            cursor.execute(createTable)
            print (global_vars.bcolors.OKGREEN + "SUCCESS: " + str(tablename) + " Table created successfully\n" + global_vars.bcolors.ENDC)
            connection.commit()
        except psycopg2.Error as e:
            print(f"Error creating table in function check_and_build_tables_dynamically: {e}")
    else:
        print(global_vars.bcolors.OKGREEN + "SUCCESS: " + str(tablename) + " table was found.\n" + global_vars.bcolors.ENDC)


def create_insert_statement(fields, table_name):
    """
    This function creates the INSERT statment

    Parameters:
        fields: Table column names
        table_name: The database table of interest

    Returns: INSERT Statement
    """
    # create the correct amount of %s placeholders
    field_placeholders = ['%s'] * len(fields)

    fieldslistToStr = ', '.join([str(elem) for elem in fields]) 

    # combine table_name with fileds and placeholders
    fmt_args = (table_name, ','.join(fields), ','.join(field_placeholders))

    statement = "INSERT INTO %s (%s) VALUES (%s) ON CONFLICT DO NOTHING;" % fmt_args

    # cursor.execute("INSERT INTO %s (%s) VALUES (%s) ON CONFLICT DO NOTHING" % fmt_args, insert_args)
    
    return statement


def insert_to_tables(
            database_info,
            jobs_data, 
            shipment_data,
            freight_data,
            invoice_data,
            purchaseOrder_data,
            db_name_cursor, 
            db_name_connection):
    """
    This function bulk INSERTS key-value data to the job, shipment, freight, invoice, and purchaseorder
    tables

    Parameters:
        database_info: Dictionary that contains database name and postgres connection information
        jobs_data: Updated Jobs row
        shipment_data: Updated shipment row
        freight_data: Updated freight row
        invoice_data: Updated invoice row
        purchaseOrder_data: Updated purchaseOrder row
        cursor: PostgreSQL database cursor 
        connection: PostgreSQL database connection

    Returns: True if successful, False is failed
    """
    cursor, connection = connectTo_DB(database_info)

    try:
        # cursor.execute(statement, records)
        # connection.commit()
        with connection:
            with cursor as cur:
                # all INSERTS are posrt of one transaction
                cur.execute(jobs_data['statement'], jobs_data['records'])
                cur.execute(shipment_data['statement'], shipment_data['records'])
                cur.execute(freight_data['statement'], freight_data['records'])
                cur.execute(invoice_data['statement'], invoice_data['records'])
                cur.execute(purchaseOrder_data['statement'], purchaseOrder_data['records'])
        return True

    except Exception as err:
        print(f"Error inserting records: {err}")
        return False
    finally:
        connection.close()


def update_job(job, clients, statuses):
    
    today = date.today()

    job['job_id'] = str(random.randint(1000, 9999))
    job['job_number'] = "JOB-2026-" + str(random.randint(1000, 9999))
    job['client_name'] =  random.choice(clients)
    job['status'] = random.choice(statuses)
    job['date_opened'] =  str(today - timedelta(days=random.randint(0, 30)))

    # Capture job Fields
    initValues_Fields_job = list(job.keys())
    
    job_insert_statement = create_insert_statement(initValues_Fields_job, 'job')

    return job, job_insert_statement

def update_shipment(shipment, job, modes, locations):

    shipment['shipment_id'] = "SHIP-" + str(random.randint(1000, 9999))
    shipment['job_id'] = job['job_id']
    shipment['mode'] = random.choice(modes)
    shipment['origin'] = random.choice(locations)
    shipment['destination'] = random.choice(locations)

    while shipment['destination'] == shipment['origin']:
        shipment['destination'] = random.choice(locations)

    shipment['eta'] = str(datetime.strptime(str(job['date_opened']), "%Y-%m-%d").date() + timedelta(days=random.randint(20, 45)))

    # Capture shipment Fields and Values
    initValues_Fields_shipment = list(shipment.keys())

    shipment_insert_statement = create_insert_statement(initValues_Fields_shipment, 'shipment')

    return shipment, shipment_insert_statement

def update_freight(freight, shipment):
    freight_insert_statement = ''

    freight['freight_id'] = "FREIGHT-" + str(random.randint(1000, 9999))
    freight['shipment_id'] = shipment['shipment_id']

    # Capture freight Fields and Values
    initValues_Fields_frieght = list(freight.keys())

    freight_insert_statement = create_insert_statement(initValues_Fields_frieght, 'freight')

    return freight, freight_insert_statement

def update_invoice(invoice, job, shipment, freight, currency, paymentStatuses):
    invoice_insert_statement = ''

    taxAmount = freight['quantity'] * .30 # 30% tax
    invoice['invoice_id'] = str(random.randint(1000, 9999))
    invoice['job_id'] = job['job_id']
    invoice['total_amount'] = freight['quantity'] + taxAmount
    invoice['currency'] = currency[shipment['origin']]
    invoice['due_date'] = str(datetime.strptime(str(job['date_opened']), "%Y-%m-%d").date() + timedelta(days=30)) # 30 days from job date opening 
    invoice['status'] = random.choice(paymentStatuses)

    # Capture invoice Fields and Values
    initValues_Fields_invoice = list(invoice.keys())

    invoice_insert_statement = create_insert_statement(initValues_Fields_invoice, 'invoice')

    return invoice, invoice_insert_statement

def update_purchaseorder(purchaseOrder, job, freight, vendors, serviceTypes):
    purchaseOrder_insert_statement = ''

    purchaseOrder['po_id'] = str(random.randint(1000, 9999))
    purchaseOrder['job_id'] = job['job_id']
    purchaseOrder['vendor_name'] = random.choice(vendors)
    purchaseOrder['amount_due_USD'] = freight['quantity'] * 160
    purchaseOrder['service_type'] = random.choice(serviceTypes)

    # Capture purchaseOrder Fields and Values
    initValues_Fields_purchaseOrder = list(purchaseOrder.keys())

    purchaseOrder_insert_statement = create_insert_statement(initValues_Fields_purchaseOrder, 'purchaseorder')

    return purchaseOrder, purchaseOrder_insert_statement

def main():

    today = date.today()
    numberofjob = 0
    numberofshipment = 1

    # jon lists
    clients = ["Client_A", "Client_B", "Client_C", "Client_D"]
    statuses = ["BOOKED", "PICKED_UP", "IN_TRANSIT", "DELIVERED"]

    # shipment lists
    modes = ["AIR", "OCEAN", "GROUND"]
    locations = ["CAVAN", "USLAX", "MXCOL"]

    # invoice list
    paymentStatuses = ["Unpaid", "Paid"]
    currency = {"USLAX":"USD", "MXCOL":"MXN", "CAVAN":"CAD"}
    
    # purchase order lists
    quantities = ["20 Pallets", "10 Cartons"]
    vendors = ["CWL", "DHL", "Maersk"]
    serviceTypes = ["Air Freight", "Ocean Freight", "Ground Freight"]
    

    # job dictionary
    job = {
        'job_id': 100,
        'job_number': "JOB-2026-" + f"{numberofjob:03d}",
        'client_name': clients[0],
        'status': statuses[0],
        'date_opened': today.strftime("%Y-%m-%d")
    }

    # shipment dictionary
    shipment = {
        'shipment_id': "SHIP-" + f"{0:03d}",	
        'job_id': job['job_id'],
        'mode': modes[0],
        'origin': locations[0],
        'destination': locations[2],
        'eta': today + timedelta(days=10) # random date between 10 - 30 days from job date opening 
    }

    # freight dictionary
    freightdescription	= "Solar Panels"
    freight = {
        'freight_id': "FREIGHT-" + f"{0:03d}",
        'shipment_id': shipment['shipment_id'],
        'description': freightdescription,
        'weight_kg': 4500,
        'volume_cbm': 22.5,
        'quantity': 20 # 20 pallets, 24 solar panels in 1 pallet
    }

    # invoice dictionary
    # Tax Amount = (Taxable Items Total) × (Tax Rate as a Decimal)
    # Actual Received Quantity x Unit Price) + Tax + Shipping
    # Invoice Total = (Taxable Items Total) + (Tax Amount) + (Non-Taxable Items)

    taxAmount = freight['quantity'] * .30 # 30% tax
    invoice = {
        'invoice_id': f"{0:03d}",
        'job_id': job['job_id'],
        'total_amount': freight['quantity'] + taxAmount,
        'currency': currency[shipment['origin']],
        'due_date': datetime.strptime(str(job['date_opened']), "%Y-%m-%d").date() + timedelta(days=30), # 30 days from job date opening 
        'status': paymentStatuses[0]
    }

    # purchase order dictionary
    purchaseOrder = {
        'po_id': f"{0:03d}",
        'job_id': job['job_id'],
        'vendor_name': vendors[0],
        'amount_due_USD': freight['quantity'] * 160, # $300 per pannel
        'service_type': serviceTypes[0]  
    }

    # Read database Json
    databe_json = "FreightTables_db.json"

    try:
        # Open the file and load the JSON data
        with open(databe_json, "r") as file:
            database_info = json.load(file)

    except FileNotFoundError:
        print("Error: The file " + databe_json + " was not found.")
    except json.JSONDecodeError as e:
        print("Error: Failed to decode JSON from the file: {e}")

    # Desired database name
    db_name = database_info['database']['databaseName']

    # Connect to the generic postgres database, check for desired database and create it if needed
    connectToPostgres_DB(database_info)

    # Connect to desired database referenced in json
    db_name_cursor, db_name_connection = connectTo_DB(database_info)

    # Check if table exists and build it if it does not exits
    for table in database_info["tables"].keys():

        # Define create table statement
        create_table = "CREATE TABLE IF NOT EXISTS " + table + " ("

        tableColumns = list(database_info["tables"][table]["columns"].keys())
        tableColumnTypes = list(database_info["tables"][table]["columns"].values())

        # Fill the SQL CREATE TABLE statement
        for index, column in enumerate(tableColumns):
            if index == 0:
                create_table += column + " " + tableColumnTypes[index].upper() + " PRIMARY KEY NOT NULL, "
            elif index < (len(tableColumns) - 1):
                create_table += column + " " + tableColumnTypes[index].upper() + ", "
            else:
                create_table += column + " " + tableColumnTypes[index].upper()

        create_table += ")"

        # Build Tables
        check_and_build_tables_dynamically(db_name_cursor, db_name_connection, table, create_table)
        
    db_name_connection.close()

    # SIMULATE DATA 

    while True:
        # ****** JOB ******
        newJob, job_insert_statement = update_job(job, clients, statuses)
        initValues_Values_job = list(newJob.values())
        jobs_data_dict = {
            'statement':job_insert_statement,
            'records':initValues_Values_job
        }

        # print job to view
        job_output = " | ".join(f"{value}" for key, value in newJob.items())
        print("JOB: " + job_output + "\n")
        
        
        # ****** SHIPMENT ******
        newShipment, shipment_insert_statement = update_shipment(shipment, job, modes, locations)
        initValues_Values_shipment = list(newShipment.values())
        shipment_data_dict = {
            'statement':shipment_insert_statement,
            'records':initValues_Values_shipment
        }

        # print shipmnet to view
        shipment_output = " | ".join(f"{value}" for key, value in newShipment.items())
        print("SHIP: " + shipment_output + "\n")


        # ****** FREIGHT ******
        newFreight, freight_insert_statement = update_freight(freight, shipment)
        initValues_Values_freight = list(newFreight.values())
        freight_data_dict = {
            'statement':freight_insert_statement,
            'records':initValues_Values_freight
        }

        # print freight to view
        freight_output = " | ".join(f"{value}" for key, value in newFreight.items())
        print("FREIGHT: " + freight_output + "\n")


        # ****** INVOICE ******
        newInvoice, invoice_insert_statement = update_invoice(invoice, job, shipment, freight, currency, paymentStatuses)
        initValues_Values_invoice = list(newInvoice.values())
        invoice_data_dict = {
            'statement':invoice_insert_statement,
            'records':initValues_Values_invoice
        }

        # print invoice to view
        invoice_output = " | ".join(f"{value}" for key, value in newInvoice.items())
        print("INVOICE: " + invoice_output + "\n")


        # ****** PURCHASE ORDER ******
        newPurchaseOrder, purchaseOrder_insert_statement = update_purchaseorder(purchaseOrder, job, freight, vendors, serviceTypes)
        initValues_Values_purchaseorder = list(newPurchaseOrder.values())
        purchaseOrder_data_dict = {
            'statement':purchaseOrder_insert_statement,
            'records':initValues_Values_purchaseorder
        }

        # print invoice to view
        purchaseOrder_output = " | ".join(f"{value}" for key, value in newPurchaseOrder.items())
        print("PO: " + purchaseOrder_output + "\n")

        print("------------------------------------------------------------------------\n")
        
        # insert records to database
        insert_to_tables(
            database_info,
            jobs_data_dict, 
            shipment_data_dict,
            freight_data_dict,
            invoice_data_dict,
            purchaseOrder_data_dict,
            db_name_cursor, 
            db_name_connection)

        time.sleep(3)

if __name__ == '__main__':
    main()