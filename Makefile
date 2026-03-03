# Variables - Senior move: centralized config
DB_PASS=de_password
POSTGRES_URL=jdbc:postgresql://127.0.0.1:5433/freightjobs

.PHONY: help up down producer spark dbt-test clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## 1. Spin up Infrastructure (Terraform)
	cd infra && terraform apply -auto-approve
	@echo "⏳ Waiting for Postgres..."
	@until nc -z 127.0.0.1 5433; do sleep 1; done
	@docker exec -it postgres psql -U de_user -d freightjobs -c "CREATE TABLE IF NOT EXISTS fct_shipment_tracking (shipment_id TEXT, last_update TIMESTAMP, current_status TEXT);"

producer: ## 2. Start python Event Producer
	cd producer && \
	export DBT_ENV_SECRET_DB_PASSWORD=$(DB_PASS) && \
	source .venv/bin/activate && \
	python3 simulateFreight.py

materialize:
#	Create materialize container and connect it to the terraform redpanda network
	@docker run -d --name materialize --network redpanda_network -p 6875:6875 materialize/materialized:latest
#	Initialize Materialize and create database sources, views, and sinks to publish to Kafka as topics 
	@psql -U materialize -h localhost -p 6875 -d materialize -f init_materialize.sql

down: ## Tear down infrastructure
	cd infra && terraform destroy -auto-approve
	docker stop materialize
	docker rm materialize

clean: ## Remove Spark checkpoints and local logs
# 	rm -rf spark/checkpoints/
# 	rm -rf dbt/freight_analytics/target/
# 	rm -rf dbt/freight_analytics/dbt_packages/
