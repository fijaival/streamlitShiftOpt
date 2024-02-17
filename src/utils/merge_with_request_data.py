
def merge_data(data_list, requests_dict):
    for item in data_list:
        employeeId = item['id']
        if employeeId in requests_dict:
            item['day_off_requests'] = requests_dict[employeeId]
    return data_list
