from models import Employee, Full_Time_Employee, ShiftScheduler
import calendar

def run_optimization(employees_data, full_time_employees_data, year, month):
    _, number_of_days = calendar.monthrange(year, month)
    work_types = ['day1', 'day2', 'day3', 'evening1', 'evening2', 'evening3']
    employees = [Employee(**data) for data in employees_data]
    full_time_employees = [Full_Time_Employee(**data) for data in full_time_employees_data]
    scheduler = ShiftScheduler(employees, full_time_employees, days=range(number_of_days), work_types=work_types,absolute_min_workers_per_day=5,year=year,month=month)
    result = scheduler.solve()
    return result