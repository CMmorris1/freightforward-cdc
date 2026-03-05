# Real-Time Freight Forwarding CDC Pipeline

A Data Engineering project bridging Software Engineering principles (Python) with modern Data Analytics (PostgreSQL, Redpanda, Debezium, Materialize, Flask API).

## 🏗️ Architecture
- **Producer (Python):** Simulates a high-state freight lifecycle (Booked -> Delivered).
- **Streaming (Redpanda):** Orchestrated via **Terraform** A C++ Kafka-compatible engine.
- **Warehouse (PostgreSQL):** Also orchestrated via **Terraform** to ensure Infrastructure as Code (IaC) consistency.
- **CDC (Debezium):** Medallion architecture (Public -> Marts) with automated data quality tests.
- **(Materialize):** Streaming database designed to consume Change Data Capture (CDC) logs from Debezium
- **(Flask API):** Lightweight and flexible web server for RESTful API with CRUD actions

## Project Directory Structure
```text
├── README.md
├── .gitignore
├── requirements.txt (Needed Project Libraries)
├── Makefile (Commands to make Terraform Containers)
├── flask_api
│   ├── flask_server
│   │   ├── models (Flask API Database Table Models)
│   │   ├──routes (Flask API CRUD Routes)
│   |   └── __init__.py (Flask App Configurations)
|   ├── logs (Location for Flask Access/Error log files)
|   ├── testing (API Routes Test Script)
|   ├── flask_api.dockerfile (File Used by Terraform to create Flask Web Server)
|   ├── README.md
|   ├── requirements.txt (Needed Flask API Libraries)
|   └──wsgi.py (Flask Web Server Application)
├── infra (Terraform Directory)
|   ├── backend.tf
|   ├── main.tf
|   └── init_materialize.sql (SQL file to create materialize sources, views, and sinks)
├── producer
│   ├── testing
│   │   └──consumeRedpandaTopics.py (Script to read Repanda materialize view topics)
│   ├── DBConfig.json (Database configuration file for freightjobs DB creation)
│   └── simulateFreight.py (Python job simulation stream producer)

```
## 🛠️ Quick Start
For visability it is advised to run each command in a seperate terminal

1. `make up` - Provisions infrastructure & schema
    
    Includes the following docker containers, all run on the same private network called "redpanda_network"

    - Redpanda Broker
    - Postgres container with CDC enabled
        - Postgres Connector
    - Debezium (Kafka Connect)
    - Redpanda Console (Web UI) for topic view
    - Materialize 
    - Flask API

2. `make producer` - Starts python event stream
    - simulateFreight.py

3. `make materialize` - Creates sources, views and sinks from Debizuim postgres updates and publishes each of them to a respective Kafka Topic

Or

## 🛠️ Local Setup
1. `cd infra && terraform apply`
2. `cd producer && source .venv/bin/activate && python3 simulateFreight.py`
4. `cd infra && psql -U materialize -h localhost -p 6875 -d materialize -f init_materialize.sql`
5. `cd producer && python3 consumeRedpandaTopics.py` 
6. `Run Flask API` (For Flask API setup, plese see ./flask_api/README.md for detailed instructions)

To consume the Respanda topics. This file is currently configured to read the freight_jobs topic
but can be modified to red the others.


