# utils.py
import streamlit as st
import pandas as pd
from typing import Optional, Any, Dict

# -------------------------
# Cached CSV / Excel parser
# -------------------------
# caches parsed result keyed by file bytes + filename
@st.cache_data(show_spinner=False)
def parse_file_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """
    Parse uploaded CSV or Excel file. Cached by (file_bytes, filename).
    Return: pandas.DataFrame
    """
    # Use BytesIO to let pandas detect CSV vs Excel more reliably
    from io import BytesIO
    buf = BytesIO(file_bytes)
    # try CSV first
    try:
        # pandas can read CSV from BytesIO but requires decoding; use read_csv on buffer
        return pd.read_csv(buf)
    except Exception:
        # reset buffer and try excel
        buf.seek(0)
        return pd.read_excel(buf)

# -------------------------
# Cached DB connection resource
# -------------------------
# Use this to cache the mysql connector object across reruns.
@st.cache_resource
def get_mysql_conn_cached(host: str, port: int, user: str, password: str, ssl_ca_path: Optional[str] = None):
    """
    Return a mysql.connector connection object (cached resource).
    Pass connection params from st.secrets.
    NOTE: keep autocommit off if you use transactions.
    """
    import mysql.connector
    cfg = dict(
        host=host,
        port=port,
        user=user,
        password=password,
        autocommit=False
    )
    if ssl_ca_path:
        cfg["ssl_ca"] = ssl_ca_path
        cfg["ssl_verify_cert"] = True
    conn = mysql.connector.connect(**cfg)
    return conn

# -------------------------
# Cached small query examples
# -------------------------
@st.cache_data(ttl=300, show_spinner=False)
def cached_simple_query(conn_params: Dict[str, Any], sql: str, params: Optional[tuple] = None):
    """
    Run a read-only query and cache results for `ttl` seconds.
    conn_params is a serializable dict (host,user,port,ssl_ca_path...), used as part of cache key.
    """
    conn = get_mysql_conn_cached(
        conn_params["host"],
        int(conn_params.get("port", 15211)),
        conn_params["user"],
        conn_params["password"],
        conn_params.get("ssl_ca_path")
    )
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    # convert to DataFrame for easy display
    return pd.DataFrame(rows)
