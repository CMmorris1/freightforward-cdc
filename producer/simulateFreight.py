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
import random
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import execute_values
from datetime import date, datetime, timedelta

tableExists_query = 'SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name=%s)'

tableExistsinSchema_query = 'SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_schema=%s AND table_name=%s)'

schemaExists_query = 'SELECT EXISTS(SELECT * FROM information_schema.schemata WHERE schema_name=%s)'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    INFO = '\033[96m'
    OKGREEN = '\033[32m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
            job_history_data,
            shipment_data,
            freight_data,
            invoice_data,
            purchaseorder_data,
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
        purchaseorder_data: Updated purchaseorder row
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
                cur.execute(job_history_data['statement'], job_history_data['records']) 
                cur.execute(shipment_data['statement'], shipment_data['records'])
                cur.execute(freight_data['statement'], freight_data['records'])
                cur.execute(invoice_data['statement'], invoice_data['records'])
                cur.execute(purchaseorder_data['statement'], purchaseorder_data['records'])
        return True

    except Exception as err:
        print(f"Error inserting records: {err}")
        return False
    finally:
        connection.close()


def create_INSERT_statement(item_Dict, itemName):

    # Capture item_Dict Fields and Values
    initValues_Fields = list(item_Dict.keys())

    insert_statement = create_insert_statement(initValues_Fields, itemName)

    return insert_statement


def main():

    today = date.today()
    numberofjob = 0
    numberofshipment = 1

    # jon lists
    clients = ["Client_A", "Client_B", "Client_C", "Client_D"]
    statuses = ["BOOKED", "PICKED_UP", "IN_TRANSIT", "DELIVERED"]

    # shipment lists
    modes = ["AIR", "OCEAN"]
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
        'job_id': None,
        'job_number': None,
        'origin': None,
        'destination': None,
        'client_name': None,
        'date_opened': None
    }

    # job history dictionary
    job_history = {
        # 'history_id': None,
        'job_id': None,
        'status': None,
        'created_at': None
    }

    # shipment dictionary
    shipment = {
        'shipment_id': None,	
        'job_id': None,
        'mode': None,
        'eta': None # random date between 10 - 30 days from job date opening 
    }

    # freight dictionaryß
    freight = {
        'freight_id': None,
        'shipment_id': None,
        'description': None,
        'weight_kg': None,
        'volume_cbm': None,
        'quantity': None # 20 pallets, 24 solar panels in 1 pallet
    }

    # invoice dictionary
    # Tax Amount = (Taxable Items Total) × (Tax Rate as a Decimal)
    # Actual Received Quantity x Unit Price) + Tax + Shipping
    # Invoice Total = (Taxable Items Total) + (Tax Amount) + (Non-Taxable Items)


    invoice = {
        'invoice_id': None,
        'job_id': None,
        'total_amount': None,
        'currency': None,
        'due_date': None, # 30 days from job date opening 
        'status': None
    }

    # purchase order dictionary
    purchaseorder = {
        'po_id': None,
        'job_id': None,
        'vendor_name': None,
        'amount_due_USD': None, # $300 per pannel
        'service_type': None  
    }

    # Read database Json
    databe_json = "DBConfig.json"

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

    # Set initial record open data
    today = date.today()
    job['date_opened'] =  str(today - timedelta(days=random.randint(0, 30)))

    while True:

        for client in clients:
        
            #Create a job for a new client
            job['job_id'] = str(random.randint(1000, 9999))
            job['job_number'] = "JOB-2026-" + str(random.randint(1000, 9999))
            job['client_name'] =  client
            job['origin'] = 'CNSHA'
            job['destination'] = random.choice(locations)
            job['date_opened'] =  str(job['date_opened'] - timedelta(days=random.randint(0, 30)))

            #Create a job history for the new client
            job_history['job_id'] = job['job_id']
            job_history['created_at'] = str(datetime.strptime(str(job['date_opened']), "%Y-%m-%d").date() + timedelta(days=random.randint(0, 6)))
            
            #Create a shipment for the new client
            shipment['shipment_id'] = "SHIP-" + str(random.randint(1000, 9999))
            shipment['job_id'] = job['job_id']
            shipment['mode'] = random.choice(modes)
            shipment['eta'] = str(datetime.strptime(str(job['date_opened']), "%Y-%m-%d").date() + timedelta(days=random.randint(20, 45)))

            #Create a freight for the new client
            freight['freight_id'] = "FREIGHT-" + str(random.randint(1000, 9999))
            freight['shipment_id'] = shipment['shipment_id']
            freight['description'] = 'Solar Panels'
            freight['weight_kg'] = 4500
            freight['volume_cbm'] = 22.5
            freight['quantity'] = 20

            #Create an invoice for the new client
            taxAmount = freight['quantity'] * .30 # 30% tax
            invoice['invoice_id'] = str(random.randint(1000, 9999))
            invoice['job_id'] = job['job_id']
            invoice['total_amount'] = freight['quantity'] + taxAmount
            invoice['currency'] = currency[job['destination']]
            invoice['due_date'] = str(datetime.strptime(str(job['date_opened']), "%Y-%m-%d").date() + timedelta(days=30)) # 30 days from job date opening 
            invoice['status'] = paymentStatuses[0] #Unpaid until delivered
            
            #Create a purchase order for the new client
            purchaseorder['po_id'] = str(random.randint(1000, 9999))
            purchaseorder['job_id'] = job['job_id']
            purchaseorder['vendor_name'] = random.choice(vendors)
            purchaseorder['amount_due_USD'] = freight['quantity'] * 160
            purchaseorder['service_type'] = random.choice(serviceTypes)

            for job_status in statuses:
                # ****** JOB ******
                job_insert_statement = create_INSERT_statement(job, 'job')
                initValues_Values_job = list(job.values())

                job_data_dict = {
                    'statement':job_insert_statement,
                    'records':initValues_Values_job
                }

                # print job to view
                job_output = " | ".join(f"{value}" for key, value in job.items())
                print("JOB: " + job_output + "\n")
                
                
                # ****** JOB HISTORY ******
                job_history['status'] =  job_status

                if statuses[1] in job_history['status']:
                    job_history['created_at'] = str(datetime.strptime(str(job_history['created_at']), "%Y-%m-%d").date() + timedelta(days=random.randint(0, 3)))
                elif statuses[2] in job_history['status']:
                    job_history['created_at'] = str(datetime.strptime(str(shipment['eta']), "%Y-%m-%d").date() - timedelta(days=random.randint(0, 3)))
                else:
                    job_history['created_at'] = str(datetime.strptime(str(job_history['created_at']), "%Y-%m-%d").date() + timedelta(days=random.randint(0, 6)))
                job_history_insert_statement = create_INSERT_statement(job_history, 'job_history')
                initValues_Values_job_history = list(job_history.values())

                job_history_data_dict = {
                    'statement':job_history_insert_statement,
                    'records':initValues_Values_job_history
                }

                # print job to view
                job_history_output = " | ".join(f"{value}" for key, value in job_history.items())
                print("JOB HISTORY: " + job_history_output + "\n")

                # ****** SHIPMENT ******
                shipment_insert_statement = create_INSERT_statement(shipment, 'shipment')
                initValues_Values_shipment = list(shipment.values())

                shipment_data_dict = {
                    'statement':shipment_insert_statement,
                    'records':initValues_Values_shipment
                }

                # print shipmnet to view
                shipment_output = " | ".join(f"{value}" for key, value in shipment.items())
                print("SHIP: " + shipment_output + "\n")


                # ****** FREIGHT ******
                freight_insert_statement = create_INSERT_statement(freight, 'freight')
                initValues_Values_freight = list(freight.values())

                freight_data_dict = {
                    'statement':freight_insert_statement,
                    'records':initValues_Values_freight
                }

                # print freight to view
                freight_output = " | ".join(f"{value}" for key, value in freight.items())
                print("FREIGHT: " + freight_output + "\n")


                # ****** INVOICE ******
                # Maybe they have paid already, or maybe not
                if paymentStatuses[0] in invoice['status'] and job_status not in statuses[3]:
                    invoice['status'] = random.choice(paymentStatuses)
                else:
                    invoice['status'] = paymentStatuses[1]

                invoice_insert_statement = create_INSERT_statement(invoice, 'invoice')
                initValues_Values_invoice = list(invoice.values())
                
                invoice_data_dict = {
                    'statement':invoice_insert_statement,
                    'records':initValues_Values_invoice
                }

                # print invoice to view
                invoice_output = " | ".join(f"{value}" for key, value in invoice.items())
                print("INVOICE: " + invoice_output + "\n")


                # ****** PURCHASE ORDER ******
                purchaseorder_insert_statement = create_INSERT_statement(purchaseorder, 'purchaseorder')
                initValues_Values_purchaseorder = list(purchaseorder.values())

                purchaseorder_data_dict = {
                    'statement':purchaseorder_insert_statement,
                    'records':initValues_Values_purchaseorder
                }

                # print invoice to view
                purchaseorder_output = " | ".join(f"{value}" for key, value in purchaseorder.items())
                print("PO: " + purchaseorder_output + "\n")

                print("------------------------------------------------------------------------\n")
                
                # insert records to database
                insert_to_tables(
                    database_info,
                    job_data_dict,
                    job_history_data_dict, 
                    shipment_data_dict,
                    freight_data_dict,
                    invoice_data_dict,
                    purchaseorder_data_dict,
                    db_name_cursor, 
                    db_name_connection)

                time.sleep(3)

if __name__ == '__main__':
    main()