import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

# 1. M1 Stability Environment Variables
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

# 2. Initialize Spark with M1-optimized settings
spark = SparkSession.builder \
    .appName("FreightForwardingPipeline") \
    .config("spark.driver.host", "localhost") \
    .config("spark.driver.bindAddress", "127.0.0.1") \
    .config("spark.sql.shuffle.partitions", "2") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.2") \
    .getOrCreate()

# 3. Define Schema (All strings initially from JSON)
schema = StructType([
    StructField("shipment_id", StringType()),
    StructField("status", StringType()),
    StructField("origin", StringType()),
    StructField("destination", StringType()),
    StructField("timestamp", StringType())
])

# 4. Read from Redpanda
raw_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:19092") \
    .option("subscribe", "freight-events") \
    .option("startingOffsets", "earliest") \
    .load()

# 5. Parse JSON and Cast Timestamp (Crucial for Watermarking)
processed_df = raw_df.selectExpr("CAST(value AS STRING)") \
    .select(F.from_json(F.col("value"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("event_ts", F.to_timestamp(F.col("timestamp"))) \
    .filter(F.col("event_ts").isNotNull())

# 6. Stateful Aggregation (Latest Status per Shipment)
shipment_status = processed_df \
    .withWatermark("event_ts", "1 minute") \
    .groupBy(
        F.window(F.col("event_ts"), "1 minute"), 
        "shipment_id"
    ) \
    .agg(
        F.max("event_ts").alias("last_update"),
        F.max("status").alias("current_status")
    )

# 7. JDBC Sink Function (Writing to Postgres on Port 5433)
def write_to_postgres(batch_df, batch_id):
    print(f"🚀 ATTEMPTING TO WRITE BATCH {batch_id} TO POSTGRES...")

    # Flatten the DataFrame (remove the 'window' struct)
    clean_df = batch_df.select("shipment_id", "last_update", "current_status")
    
    clean_df.write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://127.0.0.1:5433/analytics") \
        .option("dbtable", "fct_shipment_tracking") \
        .option("user", "de_user") \
        .option("password", "de_password") \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()
    
    print(f"✅ BATCH {batch_id} WRITTEN SUCCESSFULLY")

# 8. Start the Stream
query = shipment_status.writeStream \
    .foreachBatch(write_to_postgres) \
    .trigger(processingTime='5 seconds') \
    .option("checkpointLocation", "./spark/checkpoints/freight_analytics") \
    .outputMode("update") \
    .start()

query.awaitTermination()
