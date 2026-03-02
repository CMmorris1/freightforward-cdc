# Variables - Senior move: centralized config
DB_PASS=de_password
POSTGRES_URL=jdbc:postgresql://127.0.0.1:5433/freightjobs
# SPARK_PKGS=org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.2

.PHONY: help up down producer spark dbt-test clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## 1. Spin up Infrastructure (Terraform)
	cd infra && terraform apply -auto-approve
	@echo "⏳ Waiting for Postgres..."
	@until nc -z 127.0.0.1 5433; do sleep 1; done
	@psql -U materialize -h localhost -p 6875 -d materialize -f init_materialize.sql
# 	@docker exec -it postgres psql -U de_user -d freightjobs -c "CREATE TABLE IF NOT EXISTS fct_shipment_tracking (shipment_id TEXT, last_update TIMESTAMP, current_status TEXT);"

producer: ## 2. Start python Event Producer
	cd producer && python3 simulateFreight.py

# spark: ## 3. Start PySpark Stream
# 	export DBT_ENV_SECRET_DB_PASSWORD=$(DB_PASS) && \
# 	source .venv/bin/activate && \
# 	spark-submit --packages $(SPARK_PKGS) spark/jobs/process_freight.py

# dbt-run: ## 4. Run dbt Transformations
# 	export DBT_ENV_SECRET_DB_PASSWORD=$(DB_PASS) && \
# 	cd dbt/freight_analytics && \
# 	dbt build --profiles-dir .

down: ## Tear down infrastructure
	cd infra && terraform destroy -auto-approve

clean: ## Remove Spark checkpoints and local logs
	rm -rf spark/checkpoints/
	rm -rf dbt/freight_analytics/target/
	rm -rf dbt/freight_analytics/dbt_packages/
