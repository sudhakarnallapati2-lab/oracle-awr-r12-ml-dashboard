import streamlit as st
import os

# 🔹 Oracle DB configuration (from Streamlit secrets if available)
try:
    creds = st.secrets["oracle"]
    ORACLE_CONFIG = {
        "user": creds["user"],
        "password": creds["password"],
        "dsn": creds["dsn"]
    }
except Exception:
    ORACLE_CONFIG = {
        "user": os.getenv("ORACLE_USER", "dummy_user"),
        "password": os.getenv("ORACLE_PASSWORD", "dummy_pass"),
        "dsn": os.getenv("ORACLE_DSN", "localhost/XEPDB1")
    }

# 🔹 CSV fallback paths (local or secret)
try:
    csv_conf = st.secrets["csv"]
    CSV_PATH_AWR = {
        "summary": csv_conf.get("awr_summary", "awr_metrics.csv"),
        "sql": csv_conf.get("awr_sql", "awr_metrics_sql.csv"),
        "waits": csv_conf.get("awr_waits", "awr_waits.csv"),
    }
    CSV_PATH_R12 = csv_conf.get("workflow", "workflow_monitor_sample.csv")
except Exception:
    CSV_PATH_AWR = {
        "summary": "awr_metrics.csv",
        "sql": "awr_metrics_sql.csv",
        "waits": "awr_waits.csv",
    }
    CSV_PATH_R12 = "workflow_monitor_sample.csv"
