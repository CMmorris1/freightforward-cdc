terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.6.2"
    }
  }
}

provider "docker" {}

# --- NETWORK ---
resource "docker_network" "data_network" {
  name = "freight_network"
}

# --- REDPANDA (Streaming) ---
resource "docker_image" "redpanda" {
  name         = "docker.redpanda.com/redpandadata/redpanda:latest"
  keep_locally = true
}

resource "docker_container" "redpanda" {
  name  = "redpanda"
  image = docker_image.redpanda.image_id
  networks_advanced { name = docker_network.data_network.name }
  
  command = [
    "redpanda", "start", "--overprovisioned", "--smp", "1", "--memory", "1G",
    "--kafka-addr", "internal://0.0.0.0:9092,external://0.0.0.0:19092",
    "--advertise-kafka-addr", "internal://redpanda:9092,external://localhost:19092"
  ]

  ports {
    internal = 19092
    external = 19092
  }
}

# --- POSTGRES (Warehouse) ---
resource "docker_container" "postgres" {
  name  = "postgres"
  image = "postgres:17"
  networks_advanced { name = docker_network.data_network.name }
  
  env = [
    "POSTGRES_USER=de_user",
    "POSTGRES_PASSWORD=de_password",
    "POSTGRES_DB=analytics"
  ]

  ports {
    internal = 5432
    external = 5433
  }
}

# --- SPARK MASTER (Processing) ---
resource "docker_container" "spark_master" {
  name  = "spark-master"
  image = "apache/spark:latest"
  networks_advanced { name = docker_network.data_network.name }
  
  user = "root"
  env  = ["SPARK_NO_DAEMONIZE=true"]
  
  command = ["/opt/spark/bin/spark-class", "org.apache.spark.deploy.master.Master"]

  # Port 8080: Spark Master Web UI
  ports {
    internal = 8080
    external = 8080
  }

  # Port 7077: Spark Master spark:// URL
  ports {
    internal = 7077
    external = 7077
  }
}

# --- SPARK WORKER (Scalable Processing) ---
resource "docker_container" "spark_worker" {
  name  = "spark-worker"
  image = "apache/spark:latest"
  networks_advanced { name = docker_network.data_network.name }
  
  user = "root"
  env  = [
    "SPARK_NO_DAEMONIZE=true"
  ]
  
  # Reference the master container's name dynamically
  command = [
    "/opt/spark/bin/spark-class", 
    "org.apache.spark.deploy.worker.Worker", 
    "spark://${docker_container.spark_master.name}:7077"
  ]

  # Optional: Limit resources so your M1 Air stays responsive
  cpu_shares = 512
  memory     = 2048 # 2GB
}

