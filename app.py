import streamlit as st
import pandas as pd
import plotly.express as px
import oracledb
from config import ORACLE_CONFIG, CSV_PATH_AWR, CSV_PATH_R12

st.set_page_config(page_title="Oracle AWR + R12 Workflow ML Dashboard", layout="wide")

# ---------------------------------------------
# Utility: Oracle connection or fallback
# ---------------------------------------------
def get_oracle_connection():
    try:
        conn = oracledb.connect(
            user=ORACLE_CONFIG["user"],
            password=ORACLE_CONFIG["password"],
            dsn=ORACLE_CONFIG["dsn"]
        )
        st.success("✅ Connected to Oracle Database")
        return conn
    except Exception as e:
        st.warning(f"⚠️ Oracle not reachable, using CSV fallback. ({e})")
        return None

# ---------------------------------------------
# Cached loaders
# ---------------------------------------------
@st.cache_data
def load_awr_summary():
    try:
        return pd.read_csv(CSV_PATH_AWR["summary"])
    except Exception as e:
        st.error(f"Error loading AWR summary CSV: {e}")
        return pd.DataFrame()

@st.cache_data
def load_awr_sql():
    try:
        return pd.read_csv(CSV_PATH_AWR["sql"])
    except Exception as e:
        st.error(f"Error loading AWR SQL CSV: {e}")
        return pd.DataFrame()

@st.cache_data
def load_awr_waits():
    try:
        return pd.read_csv(CSV_PATH_AWR["waits"])
    except Exception as e:
        st.error(f"Error loading AWR waits CSV: {e}")
        return pd.DataFrame()

@st.cache_data
def load_workflow():
    try:
        return pd.read_csv(CSV_PATH_R12)
    except Exception as e:
        st.error(f"Error loading Workflow CSV: {e}")
        return pd.DataFrame()

# Optional alias for backward compatibility
def load_awr_sql_details():
    return load_awr_sql()

# ---------------------------------------------
# Dashboard Layout
# ---------------------------------------------
st.title("📊 Oracle AWR + R12 Workflow ML Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(["AWR Summary", "AWR SQL", "AWR Waits", "Workflow Monitor"])

# ---------------------------------------------
# AWR Summary Tab
# ---------------------------------------------
with tab1:
    st.header("AWR Summary Metrics")
    df_summary = load_awr_summary()
    if not df_summary.empty:
        st.dataframe(df_summary.head())
        if 'CPU_Usage' in df_summary.columns:
            fig = px.line(df_summary, x=df_summary.columns[0], y='CPU_Usage', title="CPU Usage Trend")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No AWR summary data available.")

# ---------------------------------------------
# AWR SQL Tab
# ---------------------------------------------
with tab2:
    st.header("AWR SQL Statistics")
    df_sql = load_awr_sql()
    if not df_sql.empty:
        st.dataframe(df_sql.head())
        if 'Elapsed_Time' in df_sql.columns:
            fig = px.bar(df_sql.head(10), x='SQL_ID', y='Elapsed_Time', title="Top SQL by Elapsed Time")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No AWR SQL data available.")

# ---------------------------------------------
# AWR Waits Tab
# ---------------------------------------------
with tab3:
    st.header("AWR Wait Events")
    df_waits = load_awr_waits()
    if not df_waits.empty:
        st.dataframe(df_waits.head())
        if 'Wait_Class' in df_waits.columns and 'Total_Wait_Time' in df_waits.columns:
            fig = px.bar(df_waits, x='Wait_Class', y='Total_Wait_Time', title="Wait Events Overview")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No AWR waits data available.")

# ---------------------------------------------
# Workflow Tab
# ---------------------------------------------
with tab4:
    st.header("Oracle R12 Workflow Monitoring")
    df_workflow = load_workflow()
    if not df_workflow.empty:
        st.dataframe(df_workflow.head())

        if 'Status' in df_workflow.columns:
            status_counts = df_workflow['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig = px.pie(status_counts, names='Status', values='Count', title="Workflow Status Distribution")
            st.plotly_chart(fig, use_container_width=True)

        if 'Duration' in df_workflow.columns:
            fig = px.box(df_workflow, y='Duration', title="Workflow Duration Distribution")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No workflow data available.")
