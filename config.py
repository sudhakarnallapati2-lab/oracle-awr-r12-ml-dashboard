import streamlit as st
import oracledb
import pandas as pd

def get_connection():
    try:
        creds = st.secrets["oracle"]
        # Use THIN mode (no Oracle client required)
        conn = oracledb.connect(
            user=creds["user"],
            password=creds["password"],
            dsn=creds["dsn"],
            mode=oracledb.AUTH_MODE_DEFAULT
        )
        return conn
    except Exception as e:
        st.warning(f"⚠️ Oracle DB not reachable ({e}), using CSV fallback.")
        return None
