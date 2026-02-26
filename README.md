# Real-Time Freight Forwarding Analytics Pipeline

A Senior-level Data Engineering project bridging Software Engineering principles (F#, Type Safety) with modern Data Analytics (Spark, Redpanda, dbt).

## 🏗️ Architecture
- **Producer (F#):** Simulates a high-state freight lifecycle (Booked -> Delivered) using Functional Programming to ensure event integrity.
- **Streaming (Redpanda):** A C++ Kafka-compatible engine optimized for ARM64 (M1 Mac) performance.
- **Processing (PySpark):** Stateful streaming with 10-minute event-time watermarking to calculate transit KPIs.
- **Warehouse (PostgreSQL):** Orchestrated via **Terraform** to ensure Infrastructure as Code (IaC) consistency.
- **Transformation (dbt-core):** Medallion architecture (Public -> Marts) with automated data quality tests.

## 🚀 Engineering Highlights
- **Lambda Architecture:** Handles both real-time status updates and historical lead-time modeling.
- **CI/CD:** Automated testing via **GitHub Actions** using ephemeral Postgres containers.
- **Observability:** implemented dbt freshness tests to monitor stream latency.

## 🛠️ Quick Start
Run each command in a seperate terminal for visability
1. `make up` - Provisions infrastructure & schema
2. `make producer` - Starts F# event stream
3. `make spark` - Starts PySpark processing
4. `make dbt-run` - Generates analytics models

Or

## 🛠️ Local Setup
1. `cd infra && terraform apply`
2. `cd producer && dotnet run`
3. `spark-submit --packages ... spark/jobs/process_freight.py`
4. `cd dbt/freight_analytics && dbt build --profiles-dir .`

