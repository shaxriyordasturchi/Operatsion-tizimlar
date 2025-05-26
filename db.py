import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("employees.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            firstname TEXT,
            lastname TEXT,
            action TEXT,
            timestamp TEXT,
            location TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_action(username, firstname, lastname, action, location=None):
    conn = sqlite3.connect("employees.db")
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO logs (username, firstname, lastname, action, timestamp, location) VALUES (?, ?, ?, ?, ?, ?)",
              (username, firstname, lastname, action, timestamp, location))
    conn.commit()
    conn.close()
    return timestamp

def get_logs(period='daily'):
    import pandas as pd
    from datetime import datetime, timedelta
    conn = sqlite3.connect("employees.db")
    if period == 'daily':
        start_date = datetime.now().date()
    elif period == 'weekly':
        start_date = datetime.now().date() - timedelta(days=7)
    elif period == 'monthly':
        start_date = datetime.now().date() - timedelta(days=30)
    else:
        start_date = datetime(2000, 1, 1).date()
    df = pd.read_sql_query(f"SELECT * FROM logs WHERE DATE(timestamp) >= '{start_date}'", conn)
    conn.close()
    return df
