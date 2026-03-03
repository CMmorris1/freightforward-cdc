# Variables - Senior move: centralized config
DB_PASS=de_password
POSTGRES_URL=jdbc:postgresql://127.0.0.1:5433/freightjobs
VENV = venv

PIP = $(VENV)/bin/pip

.PHONY: help up down producer spark dbt-test clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# The 'venv' target creates the virtual environment directory and installs requirements
venv:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	# Use the specific python interpreter within the venv to install packages
	$(PIP) install -r requirements.txt
	@echo "Virtual environment created and requirements installed."

up: ## 1. Spin up Infrastructure (Terraform)
	cd infra && terraform apply -auto-approve
	@echo "⏳ Waiting for Postgres..."
	@until nc -z 127.0.0.1 5433; do sleep 1; done
	@docker exec -it postgres psql -U de_user -d freightjobs -c "CREATE TABLE IF NOT EXISTS fct_shipment_tracking (shipment_id TEXT, last_update TIMESTAMP, current_status TEXT);"

# The 'producer' target uses the venv's python interpreter to run your script
producer: venv ## 2. Start python Event Producer
	@echo "Running application within venv..."
	cd producer && \
	python3 simulateFreight.py &

materialize:##	Initialize Materialize and create database sources, views, and sinks to publish to Kafka as topics 
	@cd infra && \
	until nc -z 127.0.0.1 6875; do \
		echo "Waiting for Materialize ..."; \
		sleep 1; \
	done; \
	psql -U materialize -h localhost -p 6875 -d materialize -f init_materialize.sql

down: ## Tear down Terraform Infrastructure
	cd infra && terraform destroy -auto-approve

stop: ## Stop Python data producer
	@echo "Stopping the service..."
	-pkill -f "simulateFreight.py" || true

clean: ## Remove Spark checkpoints and local logs
	@echo "Cleaning up..."
	rm -rf $(VENV)
	rm -rf __pycache__
