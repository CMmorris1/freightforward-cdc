-- Create secret password for postgres connection using postgrest password
CREATE SECRET IF NOT EXISTS pg_pass  AS 'de_password';

-- Create connection to postgres on Kafka network
CREATE CONNECTION IF NOT EXISTS pg_conn TO POSTGRES (
    HOST 'postgres',
    PORT 5432,
    USER 'de_user',
    PASSWORD SECRET pg_pass,
    DATABASE 'freightjobs'
);

-- Create the connection with PLAINTEXT protocol
CREATE CONNECTION IF NOT EXISTS redpanda_conn TO KAFKA (
    BROKER 'redpanda:9092',
    SECURITY PROTOCOL = 'PLAINTEXT'
);

-- Create the sources referencing the connection
CREATE SOURCE IF NOT EXISTS freight_jobs FROM KAFKA CONNECTION redpanda_conn (TOPIC 'db.public.job') FORMAT JSON;
CREATE SOURCE IF NOT EXISTS freight_shipment FROM KAFKA CONNECTION redpanda_conn (TOPIC 'db.public.shipment') FORMAT JSON;
CREATE SOURCE IF NOT EXISTS freight_freight FROM KAFKA CONNECTION redpanda_conn (TOPIC 'db.public.freight') FORMAT JSON;
CREATE SOURCE IF NOT EXISTS freight_invoice FROM KAFKA CONNECTION redpanda_conn (TOPIC 'db.public.invoice') FORMAT JSON;
CREATE SOURCE IF NOT EXISTS freight_purchaseorder FROM KAFKA CONNECTION redpanda_conn (TOPIC 'db.public.purchaseorder') FORMAT JSON;

-- Create Materialized Views from sources
CREATE MATERIALIZED VIEW IF NOT EXISTS freight_jobs_mv AS SELECT * FROM freight_jobs;
CREATE MATERIALIZED VIEW IF NOT EXISTS freight_shipment_mv AS SELECT * FROM freight_shipment;
CREATE MATERIALIZED VIEW IF NOT EXISTS freight_freight_mv AS SELECT * FROM freight_freight;
CREATE MATERIALIZED VIEW IF NOT EXISTS freight_invoice_mv AS SELECT * FROM freight_invoice;
CREATE MATERIALIZED VIEW IF NOT EXISTS freight_purchaseorder_mv AS SELECT * FROM freight_purchaseorder;

-- Create SINK to publish the views to redpanda
CREATE SINK IF NOT EXISTS freight_jobs_sink FROM freight_jobs_mv INTO KAFKA CONNECTION redpanda_conn (TOPIC 'freight_jobs') KEY (data) NOT ENFORCED FORMAT JSON ENVELOPE UPSERT;
CREATE SINK IF NOT EXISTS freight_shipment_sink FROM freight_shipment_mv INTO KAFKA CONNECTION redpanda_conn (TOPIC 'freight_shipment') KEY (data) NOT ENFORCED FORMAT JSON ENVELOPE UPSERT;
CREATE SINK IF NOT EXISTS freight_freight_sink FROM freight_freight_mv INTO KAFKA CONNECTION redpanda_conn (TOPIC 'freight_freight') KEY (data) NOT ENFORCED FORMAT JSON ENVELOPE UPSERT;
CREATE SINK IF NOT EXISTS freight_invoice_sink FROM freight_invoice_mv INTO KAFKA CONNECTION redpanda_conn (TOPIC 'freight_invoice') KEY (data) NOT ENFORCED FORMAT JSON ENVELOPE UPSERT;
CREATE SINK IF NOT EXISTS freight_purchaseorder_sink FROM freight_purchaseorder_mv INTO KAFKA CONNECTION redpanda_conn (TOPIC 'freight_purchaseorder') KEY (data) NOT ENFORCED FORMAT JSON ENVELOPE UPSERT;
