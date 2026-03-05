import requests
import random
import json

number = 1

# -------- CREATE ROUTES ------- #

# JOB
url = 'http://127.0.0.1:5000/jobs'
# url = 'http://127.0.0.1:8000/job/create'

# job_payload = {
#     'job_id': f"{number:04d}",
#     'job_number': 'JOB-2026-0000',
#     'origin': 'CNSHA',
#     'destination': 'MXCOL',
#     'client_name': 'Client_A',
#     'date_opened': "2026-01-01"
# }

# JOB HISTORY
# url = 'http://127.0.0.1:8000/jobhistory/create'

# jobhistory_payload = {
#     'job_id':f"{number:04d}", 
#     'status': "BOOKED", 
#     'created_at': "2026-01-03"
# }

# # SHIPMENT
# url = 'http://127.0.0.1:8000/shipment/create'

# shipment_payload = {
#     'shipment_id': "SHIP-0000",
#     'job_id': f"{number:04d}",
#     'mode': 'OCEAN',
#     'eta': '2026-01-10'
# }

# # FREIGHT
# url = 'http://127.0.0.1:8000/freight/create'

# freight_payload = {
#     'freight_id': 'FREIGHT-0000',
#     'shipment_id': "SHIP-0000",
#     'description': 'Solar Panels',
#     'volume_cbm': 4500,
#     'weight_kg': 22.5,
#     'quantity': '20'
# }

# # INVOICE
# url = 'http://127.0.0.1:8000/invoice/create'

# invoice_payload = {
#     'invoice_id': f"{number:04d}",
#     'job_id': f"{number:04d}",
#     'total_amount': 26.0,
#     'currency': 'MEX',
#     'due_date': '2026-02-01',
#     'status': "Paid"
# }


# # PURCHASE ORDER
# url = 'http://127.0.0.1:8000/purchaseorder/create'

# purchaseOrder_payload = {
#     'po_id': f"{number:04d}",
#     'job_id': f"{number:04d}",
#     'vendor_name': 'DHL',
#     'amount_due_usd': 3200,
#     'service_type': 'Air Freight'
# }


# -------- UPDATE ROUTES ------- #

# JOB
# url = 'http://127.0.0.1:8000/job/update/0001'

# job_payload = {
#     'destination': 'CAVAN',
#     'client_name': 'Client_A',
# }

# JOB HISTORY
# url = 'http://127.0.0.1:8000/job_history/update/0001' 

# jobhistory_payload = {
#     'status': "DELIVERED", 
#     'created_at': "2026-01-10"
# }

# # SHIPMENT
# url = 'http://127.0.0.1:8000/shipment/update/1'

# shipment_payload = {
#     'mode': 'AIR',
#     'eta': '2026-01-10'
# }

# # FREIGHT
# url = 'http://127.0.0.1:8000/freight/update/SHIP-0000'

# freight_payload = {
#     'description': 'Solar Panels',
#     'volume_cbm': 3500,
#     'weight_kg': 22.5,
#     'quantity': '20'
# }

# # INVOICE
# url = 'http://127.0.0.1:8000/invoice/update/0001'

# invoice_payload = {
#     'total_amount': 26.0,
#     'currency': 'USD',
#     'due_date': '2026-02-01',
#     'status': "Paid"
# }


# # PURCHASE ORDER
# url = 'http://127.0.0.1:8000/purchaseorder/update/0001'

# purchaseOrder_payload = {
#     'vendor_name': 'CWL',
#     'amount_due_usd': 3200,
#     'service_type': 'Air Freight'
# }

# -------- DELETE ROUTES ------- #

# JOB
# url = 'http://127.0.0.1:8000/job/delete/0001'

# JOB HISTORY
# url = 'http://127.0.0.1:8000/job_history/delete/5234'

# # SHIPMENT
# url = 'http://127.0.0.1:8000/shipment/delete/5234'

# # FREIGHT
# url = 'http://127.0.0.1:8000/freight/delete/FREIGHT-1951'

# # INVOICE
# url = 'http://127.0.0.1:8000/invoice/delete/3605'

# # PURCHASE ORDER
# url = 'http://127.0.0.1:8000/purchaseorder/delete/2147'


try:
    # Send the POST request with the JSON payload
    # response = requests.post(url, json=job_payload) # For CREATE
    response = requests.get(url) # For READ
    # response = requests.put(url, json=job_payload) # For UPDATE
    # response = requests.delete(url) # For DELETE

    # Raise an exception for bad status codes (4xx or 5xx)
    response.raise_for_status()

    # Parse the JSON response from the Flask app
    response_data = response.json()

    print("Status Code:", response.status_code)
    print("Response Data:", response_data)

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
