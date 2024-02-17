from .create_employee_request_data import create_employee_request_data 
from .create_temp_employee_data import create_temp_employee_data
from .merge_with_request_data import merge_data
from .create_full_time_employee_data import create_full_time_employee_data

def process_data(uploaded_file):
    requests_dict = create_employee_request_data(uploaded_file)
    temp_employee_data_list = create_temp_employee_data(uploaded_file)
    full_employee_data_list = create_full_time_employee_data(uploaded_file)

    temp_emp  = merge_data(temp_employee_data_list, requests_dict)
    full_emp = merge_data(full_employee_data_list, requests_dict)
    
    return temp_emp,full_emp
