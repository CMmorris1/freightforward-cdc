terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.6.2"
    }
    kafka-connect = {
      source  = "Mongey/kafka-connect"
      version = "0.3.0"
    }
  }
}

provider "docker" {}

# --- NETWORK ---
resource "docker_network" "data_network" {
  name = "freight_network"
}


# 1. --- POSTGRES (with logical replication) ---
resource "docker_container" "postgres" {
  name  = "postgres"
  image = "postgres:17"
  networks_advanced { name = docker_network.data_network.name }
  
  env = [
    "POSTGRES_USER=de_user",
    "POSTGRES_PASSWORD=de_password",
    "POSTGRES_DB=freightjobs"
  ]

  # Enable Logical Replication for Debezium
  command = ["postgres","-c","wal_level=logical"]

  ports {
    internal = 5432
    external = 5433
  }
}

# 2. --- Kafka (using Confluent 7.0 for Kafka 3.0 compatibility) --- 
resource "docker_container" "zookeeper" {
  name  = "zookeeper"
  image = "confluentinc/cp-zookeeper:7.0.0"
  networks_advanced { name = docker_network.data_network.name }
  env = ["ZOOKEEPER_CLIENT_PORT=2181", "ZOOKEEPER_TICK_TIME=2000"]
}

resource "docker_container" "kafka" {
  name  = "kafka"
  image = "confluentinc/cp-kafka:7.0.0"
  networks_advanced { name = docker_network.data_network.name }
  depends_on = [docker_container.zookeeper]
  env = [
    "KAFKA_BROKER_ID=1",
    "KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181",
    "KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092",
    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT",
    "KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT",
    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1"
  ]
  ports { 
    internal = 29092 
    external = 29092 
  }
}

# 3. --- Debezium Connect Container --- 
resource "docker_container" "debezium" {
  name  = "debezium"
  image = "debezium/connect:2.5" # Latest stable Debezium
  networks_advanced { name = docker_network.data_network.name }
  depends_on = [docker_container.kafka]
  env = [
    "BOOTSTRAP_SERVERS=kafka:9092",
    "GROUP_ID=1",
    "CONFIG_STORAGE_TOPIC=my_connect_configs",
    "OFFSET_STORAGE_TOPIC=my_connect_offsets",
    "STATUS_STORAGE_TOPIC=my_connect_statuses",
    "KEY_CONVERTER=org.apache.kafka.connect.json.JsonConverter",
    "VALUE_CONVERTER=org.apache.kafka.connect.json.JsonConverter",
    "CONNECT_KEY_CONVERTER_SCHEMAS_ENABLE=false",
    "CONNECT_VALUE_CONVERTER_SCHEMAS_ENABLE=false"
  ]
  ports { 
    internal = 8083
    external = 8083 
  }
}


# 4. --- Materialize Container ---
#resource "docker_container" "materialize" {
#  name  = "materialize"
#  image = "materialize/materialized:latest"
#  networks_advanced { name = docker_network.data_network.name }
#  ports { internal = 6875; external = 6875 }
#}

# 5. --- Debezium PostgreSQL Connector Configuration ---
provider "kafka-connect" {
  url = "http://localhost:8083"
}

resource "time_sleep" "wait_for_debezium" {
  depends_on = [docker_container.debezium] # Or whoever runs Kafka Connect

  create_duration = "60s" # Adjust based on how long Debezium takes to boot
}

locals {
  connector_name = "postgres-connector"
}

resource "kafka-connect_connector" "postgres_source" {
  name = "postgres-connector" 
  
  config = {
    "name"              = "postgres-connector" 
    "connector.class"   = "io.debezium.connector.postgresql.PostgresConnector"
    "database.hostname" = "postgres"
    "database.port"     = "5432"
    "database.user"     = "de_user"
    "database.password" = "de_password"
    "database.dbname"   = "freightjobs"
    "topic.prefix"      = "dbserver1"
    "plugin.name"       = "pgoutput"
  }

  # Ensure we wait for the sleep timer, not just the container start
  depends_on = [time_sleep.wait_for_debezium, docker_container.postgres]
}