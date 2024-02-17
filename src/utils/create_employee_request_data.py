import pandas as pd
from .caluculate_third_thursday import caluculate_third_thursday


def create_employee_request_data(uploaded_file, year, month):
    day_of_third_thursday = caluculate_third_thursday(year, month)
    sheet_name = 0
    df_requests = pd.read_excel(uploaded_file, sheet_name)
    requests_dict = {}
    for i, row in df_requests.iterrows():
        if i == 0:
            continue

        label = int(row.iloc[0])
        marked_days = []
        for day, value in enumerate(row[2:], start=1):
            if value == '×':
                if day != day_of_third_thursday:
                    marked_days.append(day-1)

        requests_dict[label] = marked_days

    return requests_dict
