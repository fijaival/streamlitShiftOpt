import pandas as pd

def create_temp_employee_data(uploaded_file):
    sheet_name = 1  
    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)


    df.columns = ['id','name', 'paid_off', 'weekly_days', 'over_work','full_time', 'day1', 'day2', 'day3', 'evening1', 'evening2', 'evening3','last_month_consecutive_days','last_month_period_work_days']

    df['over_work'] = df['over_work'].notna()
    df['full_time'] = df['full_time'].notna()

    work_types = ['day1', 'day2', 'day3', 'evening1', 'evening2', 'evening3']
    df['work_type'] = df.apply(lambda row: [work_types[i] for i, value in enumerate(
        row[work_types]) if pd.notna(value)], axis=1)

    data_list = df[['id','name', 'paid_off', 'weekly_days', 'over_work',
                    'full_time', 'work_type', 'last_month_consecutive_days','last_month_period_work_days']].to_dict(orient='records')
    return data_list