import pandas as pd
from db import get_logs

def generate_excel_report(period='daily'):
    df = get_logs(period)
    filename = f"{period}_report.xlsx"
    df.to_excel(filename, index=False)
    return filename
