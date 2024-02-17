import pulp

#############
# Employee Class
#############


class Employee:
    def __init__(self,
                 id,
                 name,
                 paid_off,
                 weekly_days,
                 over_work,
                 full_time,
                 work_type,
                 last_month_consecutive_days,
                 last_month_period_work_days,
                 day_off_requests):
        self.id = id
        self.name = name
        self.paid_off = paid_off
        self.weekly_days = weekly_days
        self.over_work = over_work
        self.full_time = full_time
        self.work_type = work_type
        self.last_month_consecutive_days = last_month_consecutive_days
        self.last_month_period_work_days = last_month_period_work_days
        self.day_off_requests = day_off_requests
        self.shift_vars = {}
        self.assigned_vars = {}
        self.paid_vars = {}
        self.penalty_vars = {}
        self.first_week_penalty_vars = 0

    def create_shift_variables(self, days, work_types):
        # shift_vars（特定のシフトに入っているか否か）
        for day in days:
            for work_type in work_types:
                var_name = f"x({self.id},{day},{work_type})"
                self.shift_vars[(day, work_type)] = pulp.LpVariable(
                    var_name, 0, 1, cat="Binary")

        # assigned_vars（特定の日付に１つ以上の業務に入っているか否か）
        for day in days:
            var_name = f"x({self.id},{day})"
            self.assigned_vars[day] = pulp.LpVariable(
                var_name, 0, 1, cat="Binary")

        # paid_vars（特定の日が有給か否か）
        for day in days:
            var_name = f"x({self.id},{day}) is paid"
            self.paid_vars[day] = pulp.LpVariable(var_name, 0, 1, cat="Binary")

    def create_penalty_variables(self, weeks_in_month):
        # 週当たりの業務日数超過のペナルティ
        for week in range(weeks_in_month):
            var_name = f"penalty({self.id},{week})"
            self.penalty_vars[week] = pulp.LpVariable(
                var_name, 0, 1, cat="Binary")

        var_name = f"first_week_penalty({self.id})"
        self.first_week_penalty_vars = pulp.LpVariable(
            var_name, 0, 1, cat="Binary")
