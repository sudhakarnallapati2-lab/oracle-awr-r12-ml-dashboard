import os

ORACLE_CONFIG = {
    "username": os.getenv("ORACLE_USER", "system"),
    "password": os.getenv("ORACLE_PASS", "oracle"),
    "dsn": os.getenv("ORACLE_DSN", "localhost/orclpdb1")
}

CSV_PATH_AWR = "awr_metrics.csv"
CSV_PATH_AWR_SQL = "awr_metrics_sql.csv"
CSV_PATH_R12 = "workflow_monitor_sample.csv"
