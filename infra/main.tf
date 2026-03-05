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

# 2. Define a Redpanda Broker container
resource "docker_container" "redpanda" {
  name  = "redpanda"
  image = docker_image.redpanda.name
  command = [
    "redpanda", "start", "--overprovisioned", 
    "--kafka-addr", "internal://0.0.0.0:9092,external://0.0.0.0:19092", 
    "--advertise-kafka-addr", "internal://redpanda:9092,external://127.0.0.1:19092", 
    "--smp", "1", "--memory", "1G", "--reserve-memory", "0M", "--node-id", "0", "--check=false"]

  networks_advanced { 
    name = docker_network.kafka_net.name 
  }

    ports { 
    internal = 19092 
    external = 19092 
  }
  
  ports { 
    internal = 9092 
    external = 9092 
  }
}

# 3. Define a Postgres container with CDC enabled
resource "docker_container" "postgres" {
  name    = "postgres"
  image   = "postgres:17"
  command = ["postgres", "-c", "wal_level=logical"]
  env     = ["POSTGRES_USER=de_user", "POSTGRES_PASSWORD=de_password", "POSTGRES_DB=freightjobs"]
  
  networks_advanced { 
    name = docker_network.kafka_net.name 
  }

  ports { 
    internal = 5432
    external = 5433
  }
}

# 4. Define a Debezium (Kafka Connect) container
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

  networks_advanced { 
    name = docker_network.kafka_net.name 
  }

  ports { 
    internal = 8083 
    external = 8083 
  }
  depends_on = [docker_container.redpanda]
}

# 5. Define a Redpanda Console (Web UI)
resource "docker_container" "console" {
  name  = "redpanda-console"
  image = docker_image.redpanda.name
  env = [
    "KAFKA_BROKERS=redpanda:9092",
    "KAFKA_CONNECT_ENABLED=true",
    "KAFKA_CONNECT_CLUSTERS_0_NAME=debezium",
    "KAFKA_CONNECT_CLUSTERS_0_URL=http://connect:8083"
  ]

  networks_advanced { 
    name = docker_network.kafka_net.name 
  }

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


# 7. Define a Postgres Connector
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


resource "time_sleep" "wait_50_seconds" {
  create_duration = "50s"
  depends_on      = [docker_container.redpanda]
}

# 8. Define the Materialize Docker image
resource "docker_image" "materialize" {
  name = "materialize/materialized:latest" # Replace with your preferred version
}

# Define the Materialize container
resource "docker_container" "materialize" {
  name  = "materialize"
  image = docker_image.materialize.image_id

  # Materialize default SQL port
  ports {
    internal = 6875
    external = 6875
  }

  # Materialize default HTTP/Console port
  ports {
    internal = 8080
    external = 6874
  }

  # Connect to the same network as Redpanda and Postgres
  networks_advanced {
    name = docker_network.kafka_net.name
  }

  # Optional: Persistence if needed
  # volumes {
  #   container_path = "/var/lib/materialize"
  #   host_path      = "${path.cwd}/mzdata"
  # }


  depends_on = [
    time_sleep.wait_50_seconds,
    docker_container.redpanda,
    docker_container.postgres
  ]
}

# 9. Define the Flask API Container
resource "docker_image" "flask_image" {
  name = "flask-api-image"
  build {
    # Path from your main.tf to the flask_api folder
    context = "/Users/ChrisProjects/Documents/Learning/Data_Engineering/FreightForward_CDC/flask_api" 
    dockerfile = "flask_api.dockerfile" 
  }
}

resource "docker_container" "flask_api" {
  name  = "flask-crud-api"
  image = docker_image.flask_image.image_id


  networks_advanced {
    name = docker_network.kafka_net.name
  }

  ports {
    internal = 5000
    external = 5000
  }
  
  env = [
    "FLASK_APP=wsgi.py",
    "FLASK_RUN_HOST=0.0.0.0", # Set host address here
    "FLASK_RUN_PORT=5000", # Set port here
    "SQLALCHEMY_DATABASE_URI=postgresql://de_user:de_password@postgres:5432/freightjobs",
    "DATABASE_SCHEMA=public",
    "HTTPS_ENABLED=0",
    "VERIFY_USER=1",
    "FLASK_DEBUG=1",
    "REDPANDA_BROKERS=redpanda:9092",
    "OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES"
  ]

  # Ensure the API only starts after the DB is ready
  must_run = true
}

output "flask_api_url" {
  value = "http://localhost:${docker_container.flask.ports[0].external}"
}