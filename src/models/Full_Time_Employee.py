import pulp

#####################
# full time employee
#####################
class Full_Time_Employee:
    def __init__(self, id, name, paid_off, holiday_count_per_month, last_month_consecutive_days, day_off_requests):
        self.id = id
        self.name = name
        self.paid_off = paid_off
        self.holiday_count_per_month = holiday_count_per_month
        self.last_month_consecutive_days = last_month_consecutive_days
        self.day_off_requests = day_off_requests
        self.shift_vars = {}
        self.paid_vars = {}

    def create_shift_variables(self, days):
        for day in days:
            var_name = f"x({self.id},{day})"
            self.shift_vars[day] = pulp.LpVariable(var_name,0, 1, cat="Binary")

        #paid_vars（特定の日が有給か否か）
        for day in days:
            var_name = f"x({self.id},{day}) is paid"
            self.paid_vars[day] = pulp.LpVariable(var_name,0, 1, cat="Binary")
