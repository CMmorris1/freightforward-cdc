# Real-Time Freight Forwarding Analytics Pipeline

A Data Engineering project bridging Software Engineering principles (Python) with modern Data Analytics (PostgreSQL, Redpanda, Debezium, Materialize, Flask API).

## 🏗️ Architecture
- **Producer (Python):** Simulates a high-state freight lifecycle (Booked -> Delivered).
- **Streaming (Redpanda):** Orchestrated via **Terraform** A C++ Kafka-compatible engine.
- **Warehouse (PostgreSQL):** Also orchestrated via **Terraform** to ensure Infrastructure as Code (IaC) consistency.
- **CDC (Debezium):** Medallion architecture (Public -> Marts) with automated data quality tests.
- **(Materialize):** Streaming database designed to consume Change Data Capture (CDC) logs from Debezium
- **(Flask API):** Lightweight and flexible web server for RESTful API with CRUD actions

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

## To consume the Respanda topics. This file is currently configured to read the freight_jobs topic
## it can be modified by uncommenting other topics and replacing the desired topic in line 32
5. `cd producer && python3 consumeRedpandaTopics.py` 

## For Flask API setup, plese see ./flask_api/README.md for detailed instructions
6. Run Flask API 


