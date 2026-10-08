-- Main analytical table using the MergeTree engine
CREATE TABLE IF NOT EXISTS default.system_events (
    timestamp DateTime64(3, 'UTC') DEFAULT now64(3),
    service_name LowCardinality(String),
    event_type LowCardinality(String),
    environment LowCardinality(String),
    payload String,
    latency_ms UInt16
) ENGINE = MergeTree()
PRIMARY KEY (service_name, event_type)
ORDER BY (service_name, event_type, timestamp);

-- Dead Letter Queue table for storing malformed raw payloads
CREATE TABLE IF NOT EXISTS default.system_events_dlq (
    failed_at DateTime64(3, 'UTC') DEFAULT now64(3),
    raw_payload String,
    error_message String
) ENGINE = MergeTree()
ORDER BY failed_at;