# Real-Time Freight Forwarding Analytics Pipeline

A Data Engineering project bridging Software Engineering principles (Python) with modern Data Analytics (PostgreSQL, Redpanda, Debezium, Materialize).

## 🏗️ Architecture
- **Producer (Python):** Simulates a high-state freight lifecycle (Booked -> Delivered).
- **Streaming (Redpanda):** Orchestrated via **Terraform** A C++ Kafka-compatible engine.
- **Warehouse (PostgreSQL):** Also orchestrated via **Terraform** to ensure Infrastructure as Code (IaC) consistency.
- **CDC (Debezium):** Medallion architecture (Public -> Marts) with automated data quality tests.

## 🚀 Engineering Highlights
- **Lambda Architecture:** Handles both real-time status updates and historical lead-time modeling.
- **CI/CD:** Automated testing via **GitHub Actions** using ephemeral Postgres containers.

## 🛠️ Quick Start
Run each command in a seperate terminal for visability
1. `make up` - Provisions infrastructure & schema
2. `make producer` - Starts python event stream
3. `make materialize` - Creates sources, views and sinks from Debizuim postgres updates and publishes each of them to a respective Kafka Topic

Or

## 🛠️ Local Setup
1. `cd infra && terraform apply`
2. `cd producer && source .venv/bin/activate && python3 simulateFreight.py`
4. `cd infra && psql -U materialize -h localhost -p 6875 -d materialize -f init_materialize.sql`


