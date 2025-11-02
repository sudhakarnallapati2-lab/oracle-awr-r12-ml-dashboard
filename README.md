Oracle Monitoring (AWR + R12 Workflow) — Streamlit App
======================================================

Contents:
- app.py                : Combined Streamlit app for AWR and Oracle R12 Workflow monitoring
- config.py             : Configuration for Oracle connection and CSV fallbacks
- requirements.txt      : Python requirements
- awr_metrics.csv       : Sample AWR summary CSV (fallback)
- awr_metrics_sql.csv   : Sample AWR SQL-level CSV (fallback)
- workflow_monitor_sample.csv : Sample Workflow CSV (fallback)

Usage:
1. Install dependencies:
   pip install -r requirements.txt

2. (Optional) Set Oracle connection environment variables:
   export ORACLE_USER=apps
   export ORACLE_PASS=apps
   export ORACLE_DSN=host:1521/servicename

3. Run:
   streamlit run app.py

Notes:
- The app tries to connect to Oracle using cx_Oracle. If that fails it loads the CSV fallback files.
- Replace sample CSVs with real exports if you don't want to enable DB connectivity.
