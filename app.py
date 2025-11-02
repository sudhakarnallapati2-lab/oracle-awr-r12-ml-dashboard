import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import cx_Oracle
from config import ORACLE_CONFIG, CSV_PATH_AWR, CSV_PATH_R12
import altair as alt
from datetime import datetime

st.set_page_config(page_title="Oracle Monitoring (AWR + R12 Workflow)", layout="wide")
st.title("🔎 Oracle Monitoring — AWR & R12 Workflow (ML-backed)")

# -----------------------------
# Helper loaders
# -----------------------------
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
        st.error(f"Error loading workflow CSV: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_workflow_data():
    try:
        conn = cx_Oracle.connect(
            ORACLE_CONFIG['username'],
            ORACLE_CONFIG['password'],
            ORACLE_CONFIG['dsn']
        )
        query = """SELECT 
                    i.item_type,
                    i.item_key,
                    i.begin_date,
                    i.end_date,
                    (i.end_date - i.begin_date) * 24 * 60 AS duration_minutes,
                    s.activity_name,
                    s.activity_status,
                    nvl(n.notification_status, 'NONE') AS notification_status
                FROM wf_items i
                JOIN wf_item_activity_statuses s ON i.item_key = s.item_key
                LEFT JOIN wf_notifications n ON s.notification_id = n.notification_id
                WHERE i.begin_date > SYSDATE - 7"""
        df = pd.read_sql(query, conn)
        conn.close()
        st.success("Loaded Workflow data from Oracle R12")
        return df
    except Exception as e:
        st.warning(f"Oracle R12 load failed: {e}")
        st.info("Loading Workflow from CSV fallback")
        return pd.read_csv(CSV_PATH_R12)

# -----------------------------
# Simple training utilities
# -----------------------------
def train_summary_model(df):
    features = ['DB_CPU', 'DB_TIME', 'EXECS', 'BUFFER_GETS', 'PHYS_READS']
    df = df.dropna(subset=features)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[features])
    model = IsolationForest(contamination=0.05, random_state=42)
    df['anomaly'] = model.fit_predict(scaled)
    df['anomaly_label'] = df['anomaly'].map({1: 'Normal', -1: 'Anomaly'})
    return df

def train_workflow_model(df):
    df['duration_minutes'] = df['duration_minutes'].fillna(0)
    features = ['duration_minutes']
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[features])
    model = IsolationForest(contamination=0.05, random_state=42)
    df['anomaly'] = model.fit_predict(scaled)
    df['anomaly_label'] = df['anomaly'].map({1: 'Normal', -1: 'Delayed'})
    return df

# -----------------------------
# Load data
# -----------------------------
st.sidebar.header("Controls")
refresh_rate = st.sidebar.slider("Auto-refresh (minutes)", 1, 10, 3)
st.sidebar.markdown("Set environment variables ORACLE_USER / ORACLE_PASS / ORACLE_DSN in your runtime to enable DB mode.")
st.markdown(f"<meta http-equiv='refresh' content='{refresh_rate * 60}'>", unsafe_allow_html=True)

awr_summary = load_awr_summary()
awr_sql = load_awr_sql_details()
workflow = load_workflow_data()

# parse times if present
if 'BEGIN_INTERVAL_TIME' in awr_summary.columns:
    try:
        awr_summary['BEGIN_INTERVAL_TIME'] = pd.to_datetime(awr_summary['BEGIN_INTERVAL_TIME'])
    except:
        pass

if 'begin_date' in workflow.columns:
    try:
        workflow['begin_date'] = pd.to_datetime(workflow['begin_date'])
        workflow['end_date'] = pd.to_datetime(workflow['end_date'])
    except:
        pass

# Train models
awr_summary = train_summary_model(awr_summary)
workflow = train_workflow_model(workflow)

# -----------------------------
# Layout: Tabs for AWR and Workflow
# -----------------------------
tabs = st.tabs(['AWR Overview', 'AWR SQL Breakdown', 'R12 Workflow'])

# AWR Overview
with tabs[0]:
    st.header('AWR — Instance-level Anomaly Detection')
    st.dataframe(awr_summary.head())
    chart = alt.Chart(awr_summary).mark_circle(size=60).encode(
        x='DB_CPU:Q', y='DB_TIME:Q', color='anomaly_label:N',
        tooltip=['SNAP_ID', 'DB_CPU', 'DB_TIME', 'EXECS', 'BUFFER_GETS', 'anomaly_label']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

    if 'BEGIN_INTERVAL_TIME' in awr_summary.columns:
        st.subheader('Anomaly Trend Over Time (DB_CPU)')
        trend = alt.Chart(awr_summary).mark_line(point=True).encode(
            x='BEGIN_INTERVAL_TIME:T', y='DB_CPU:Q', color='anomaly_label:N',
            tooltip=['BEGIN_INTERVAL_TIME', 'DB_CPU', 'DB_TIME', 'anomaly_label']
        ).interactive()
        st.altair_chart(trend, use_container_width=True)

    st.subheader('Summary Stats')
    col1, col2 = st.columns(2)
    col1.metric('Normal snapshots', int(awr_summary[awr_summary['anomaly_label']=='Normal'].shape[0]))
    col2.metric('Anomalous snapshots', int(awr_summary[awr_summary['anomaly_label']=='Anomaly'].shape[0]))

# AWR SQL Breakdown
with tabs[1]:
    st.header('AWR — SQL-level Breakdown')
    st.write('Use this to inspect top SQLs for anomalous snapshots.')
    anomaly_snaps = awr_summary[awr_summary['anomaly_label']=='Anomaly']['SNAP_ID'].unique().tolist()
    selected_snap = st.selectbox('Select Anomalous SNAP_ID', anomaly_snaps if anomaly_snaps else [None])
    if selected_snap is not None:
        sql_filtered = awr_sql[awr_sql['SNAP_ID']==selected_snap]
        if not sql_filtered.empty:
            sql_top = sql_filtered.sort_values('ELAPSED_SEC', ascending=False).head(20)
            chart_sql = alt.Chart(sql_top).mark_bar().encode(
                x='ELAPSED_SEC:Q', y=alt.Y('SQL_ID:N', sort='-x'),
                tooltip=['SQL_ID','ELAPSED_SEC','EXECUTIONS','BUFFER_GETS','PHYS_READS']
            )
            st.altair_chart(chart_sql, use_container_width=True)
            st.dataframe(sql_top)
        else:
            st.info('No SQL data for this snapshot (check CSV fallback files).')

# R12 Workflow tab
with tabs[2]:
    st.header('Oracle R12 Workflow Monitoring')
    st.dataframe(workflow.head())
    chart = alt.Chart(workflow).mark_circle(size=60).encode(
        x='activity_name:N', y='duration_minutes:Q', color='anomaly_label:N',
        tooltip=['item_type','item_key','activity_name','duration_minutes','anomaly_label']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

    st.subheader('Status counts')
    st.write(workflow['anomaly_label'].value_counts())

# Exports
st.sidebar.subheader('Exports')
st.sidebar.download_button('Download AWR Summary CSV', data=awr_summary.to_csv(index=False).encode('utf-8'),
                           file_name=f'awr_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
st.sidebar.download_button('Download AWR SQL CSV', data=awr_sql.to_csv(index=False).encode('utf-8'),
                           file_name=f'awr_sql_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
st.sidebar.download_button('Download Workflow CSV', data=workflow.to_csv(index=False).encode('utf-8'),
                           file_name=f'workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

st.caption(f'Last refreshed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
