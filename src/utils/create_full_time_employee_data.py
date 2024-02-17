import pandas as pd

def create_full_time_employee_data(uploaded_data):
    sheet_name = 2
    df_full = pd.read_excel(uploaded_data, sheet_name=sheet_name)

    df_full.columns = ['id','name', 'paid_off', 'holiday_count_per_month',"last_month_consecutive_days"]
    full_emp_dict = df_full.to_dict(orient='records')

    return full_emp_dict