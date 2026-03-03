terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0.2" }
    kafka-connect = { source = "Mongey/kafka-connect", version = "0.4.3" }
  }
}

provider "docker" {
  # If you are on Mac, leaving this blank lets it use the default socket.
  # If you must be explicit:
  host = "unix:///var/run/docker.sock"
}

# 1. Define the Private Network
resource "docker_network" "kafka_net" {
  name = "redpanda_network"
}

# --- REDPANDA (Streaming) ---
resource "docker_image" "redpanda" {
  name         = "docker.redpanda.com/redpandadata/redpanda:latest"
  keep_locally = true
}

# 2. Redpanda Broker
resource "docker_container" "redpanda" {
  name  = "redpanda"
  image = docker_image.redpanda.name
  command = [
    "redpanda", "start", "--overprovisioned", 
    "--kafka-addr", "internal://0.0.0.0:9092,external://0.0.0.0:19092", 
    "--advertise-kafka-addr", "internal://redpanda:9092,external://127.0.0.1:19092", 
    "--smp", "1", "--memory", "1G", "--reserve-memory", "0M", "--node-id", "0", "--check=false"]
  networks_advanced { name = docker_network.kafka_net.name }
    ports { 
    internal = 19092 
    external = 19092 
  }
  
  ports { 
    internal = 9092 
    external = 9092 
  }
}

# 3. Postgres with CDC enabled
resource "docker_container" "postgres" {
  name    = "postgres"
  image   = "postgres:17"
  command = ["postgres", "-c", "wal_level=logical"]
  env     = ["POSTGRES_USER=de_user", "POSTGRES_PASSWORD=de_password", "POSTGRES_DB=freightjobs"]
  networks_advanced { name = docker_network.kafka_net.name }
  ports { 
    internal = 5432
    external = 5433
  }
}

# 4. Debezium (Kafka Connect)
resource "docker_container" "debezium" {
  name  = "debezium"
  image = "quay.io/debezium/connect:2.7.0.Final"
  env = [
    "BOOTSTRAP_SERVERS=redpanda:9092",
    "GROUP_ID=1",
    "CONFIG_STORAGE_TOPIC=my_configs",
    "OFFSET_STORAGE_TOPIC=my_offsets",
    "STATUS_STORAGE_TOPIC=my_status"
  ]
  # This checks if the /connectors endpoint is actually reachable
  healthcheck {
    test     = ["CMD", "curl", "-f", "http://localhost:8083/connectors"]
    interval = "10s"
    retries  = 20
    timeout  = "5s"
  }
  networks_advanced { name = docker_network.kafka_net.name }
  ports { 
    internal = 8083 
    external = 8083 
  }
  depends_on = [docker_container.redpanda]
}

# 5. Redpanda Console (Web UI)
resource "docker_container" "console" {
  name  = "redpanda-console"
  image = docker_image.redpanda.name
  env = [
    "KAFKA_BROKERS=redpanda:9092",
    "KAFKA_CONNECT_ENABLED=true",
    "KAFKA_CONNECT_CLUSTERS_0_NAME=debezium",
    "KAFKA_CONNECT_CLUSTERS_0_URL=http://connect:8083"
  ]
  networks_advanced { name = docker_network.kafka_net.name }
  ports { 
    internal = 8080
    external = 8080 
  }
}

# 6. Wait for the API to boot up
resource "time_sleep" "wait_60_seconds" {
  create_duration = "90s"
  depends_on      = [docker_container.debezium]
}


# 7. Configure the Postgres Connector
provider "kafka-connect" { url = "http://localhost:8083" }

resource "kafka-connect_connector" "postgres-cdc"{
  name = "postgres-cdc"
  config = {
    "name"              = "postgres-cdc"
    "connector.class"   = "io.debezium.connector.postgresql.PostgresConnector"
    "database.hostname" = "postgres"
    "database.port"     = "5432"
    "database.user"     = "de_user"
    "database.password" = "de_password"
    "database.dbname"   = "freightjobs"
    "topic.prefix"      = "db"
    "plugin.name"       = "pgoutput"
  }
  depends_on = [time_sleep.wait_60_seconds]
}

