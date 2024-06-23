import numpy as np
import pandas as pd
import pulp
import math
import calendar
from openpyxl import load_workbook
from openpyxl.styles import Font, Border, Side
import re
import json
from datetime import datetime


##########################
# ShiftScheduler Class
##########################

class ShiftScheduler:
    def __init__(self, temp_emp, full_emp, days, work_types, absolute_min_workers_per_day, year, month):
        self.employees = temp_emp
        self.full_time_employees = full_emp
        self.days = days
        self.work_types = work_types
        self.prob = pulp.LpProblem("ShiftScheduling", pulp.LpMinimize)
        self.absolute_min_workers_per_day = absolute_min_workers_per_day
        self.sacrificed_work = "evening1"
        self.year = year
        self.month = month
        self.penalty_vars = {}

    def create_variables(self):
        _, _, weeks_in_month = self.caluculate_days()
        for employee in self.employees:
            employee.create_shift_variables(self.days, self.work_types)
            employee.create_penalty_variables(weeks_in_month)
        for full_time_employee in self.full_time_employees:
            full_time_employee.create_shift_variables(self.days)

        # ５人体制となるペナルティ設定
        for day in self.days:
            var_name = f"penalty_d_{day}"
            self.penalty_vars[day] = pulp.LpVariable(var_name, 0, 1, cat="Binary")

    # 目的関数の設定

    def set_objective(self):
        _, _, weeks_in_month = self.caluculate_days()
        penalty_for_not_assigning_sacrificed_work = 100
        penalty_for_over_work = 200
        self.prob += pulp.lpSum(
            employee.shift_vars[day, work_type]
            for employee in self.employees
            for day in self.days
            for work_type in self.work_types
        ) + pulp.lpSum(
            penalty_for_over_work * employee.penalty_vars[week]
            for employee in self.employees
            if employee.over_work
            for week in range(weeks_in_month)
            for work_type in self.work_types
        ) + pulp.lpSum(
            penalty_for_not_assigning_sacrificed_work * self.penalty_vars[day]
            for day in self.days
        ) + pulp.lpSum(
            1000000000 * employee.first_week_penalty_vars
            for employee in self.employees
        )

    def caluculate_days(self):
        # 第一月曜日の日付返す

        first_day_of_month = datetime(self.year, self.month, 1)
        first_sunday = 1 if first_day_of_month.weekday() == 6 else 7 - first_day_of_month.weekday()
        first_sunday = first_sunday - 1

        days_in_month = len(self.days) - 1
        weeks_in_month = math.floor((days_in_month - first_sunday+1) / 7)
        print(first_sunday, days_in_month, weeks_in_month)
        return first_sunday, days_in_month, weeks_in_month

    ###################################
    # 制約関数
    ###################################

    def add_constraints(self):
        # 割り当てがない作業に対するペナルティの制約を追加
        self.add_constraint_for_unassigned_work_penalty()

        # 従業員の休み希望に関する制約を追加
        self.add_constraint_for_day_off_requests()

        # 一人の従業員に一日一つの作業の制約を追加
        self.add_constraint_for_one_worker_per_day()

        # 一日に最低限必要な従業員数の制約を追加
        self.add_constraint_for_minimum_workers_per_day()

        # 作業タイプごとに最低限必要な従業員数の制約を追加
        self.add_constraint_for_minimum_workers_per_worktype()

        # 有給休暇の日には仕事を割り当てない制約を追加
        self.add_constraint_for_no_work_on_paid_off()

        # 従業員ができる仕事のみを割り当てる制約を追加
        self.add_constraint_for_allowed_work_types()

        # 一週間当たりの業務数制限を設定する制約を追加
        self.add_constraint_for_weekly_working_days()

        # 1日単位で出勤したかどうかを管理する変数assigned_varsを設定する制約を追加
        self.add_constraint_for_daily_assignment()

        # 5日連続の勤務を禁止する制約を追加
        self.add_constraint_for_no_consecutive_work_days()

        # フルタイムでない場合は3日連続を禁止
        self.add_constraint_for_no_consecutive_work_3days()

        # 第三木曜日は全員出勤するようにする制約を追加
        self.add_constraint_for_all_employees_third_thursday_attendance()

        # 各従業員個別の制約条件を追加
        self.add_constraint_for_individual_employee()

        # 先月分のシフトを考慮した一週間当たりの業務数制限を設定する制約を追加
        self.add_constraint_for_weekly_working_days_informed_by_last_month_shift()

        # 先月分のシフトを考慮した5日連続の勤務を禁止する制約を追加
        self.add_constraint_for_no_consecutive_work_days_informed_by_last_month_shift()

        # 先月分を考慮した従業員の個別制約を追加
        self.add_constraint_for_individual_employee_informed_by_last_month_shift()

        # 常勤従業員は特定の日に出勤するようにする制約を追加
        self.add_constraint_for_work_day_for_full_time_emp()

        # 常勤従業員は月に指定された回数だけ休むようにする制約を追加
        self.add_constraint_for_holiday_count_for_full_time_emp()

        # 常勤従業員に対して指定された回数の有給を与える制約を追加
        self.add_constraint_for_paid_off_for_full_time_emp()

        # 常勤従業員に対して5連勤を禁止する制約を追加
        self.add_constraint_for_no_consecutive_work_days_for_full_time_emp()

        # 常勤従業員に対して先月分のシフトを考慮して5日連続の勤務を禁止する制約を追加
        self.add_constraint_for_no_consecutive_work_days_informed_by_last_month_shift_for_full_time_emp()

        # 常勤従業員に対してシフト希望を守る制約を追加
        self.add_constraint_for_day_off_requests_for_full_time_emp()

    def add_constraint_for_unassigned_work_penalty(self):
        # sacrificed_workに割り当てがない時に、該当の日付にペナルティを加える
        for day in self.days:
            self.prob += (
                pulp.lpSum(employee.shift_vars[day, self.sacrificed_work]
                           for employee in self.employees) + self.penalty_vars[day] >= 1,
                f"Penalty_if_no_{self.sacrificed_work}_on_day_{day}"
            )

        # 超過労働をした場合のペナルティ
        first_sunday, days_in_month, weeks_in_month = self.caluculate_days()
        for employee in self.employees:
            for week in range(weeks_in_month):
                start_day = first_sunday + week * 7
                end_day = start_day + 7
                if employee.over_work:
                    over_work_condition = pulp.lpSum(employee.shift_vars[(day, work_type)]
                                                     for day in range(start_day, end_day)
                                                     for work_type in self.work_types) - employee.weekly_days
                    self.prob += (over_work_condition-2)/10 <= employee.penalty_vars[week]
                    # オーバー２回までならペナルティなし。employee.penalty_varsは0,1なのでover_work_conditionが3以上になると1になる.

    # 従業員の休み希望に関する制約

    def add_constraint_for_day_off_requests(self):
        for employee in self.employees:
            for day in employee.day_off_requests:
                self.prob += employee.assigned_vars[day] <= 0

    # 同一従業員は１日に１つ(or2つ)の業務

    def add_constraint_for_one_worker_per_day(self):
        for day in self.days:
            for employee in self.employees:
                if not employee.full_time:
                    self.prob += pulp.lpSum(
                        employee.shift_vars[day, work_type] for work_type in self.work_types
                    ) <= 1, f"{employee}_{day}_can_one_work"
                else:
                    self.prob += pulp.lpSum(
                        employee.shift_vars[day, work_type] for work_type in self.work_types
                    ) <= 2, f"{employee}_{day}_can_two_work"
                    self.prob += pulp.lpSum(
                        employee.shift_vars[day, self.work_types[i]] for i in range(3)
                    ) <= 1, f"{employee}_{day}_can_one_daywork"
                    self.prob += pulp.lpSum(
                        employee.shift_vars[day, self.work_types[i]] for i in range(3, 6)
                    ) <= 1, f"{employee}_{day}_can_one_eveningwork"

    # 一日に最低限必要な従業員数の制約
    # 非常勤が６人いるが、sacrificed_workには人が入っていないときに、常勤従業員が休むことを許容してしまっている
    def add_constraint_for_minimum_workers_per_day(self):
        for day in self.days:
            temp_emp = pulp.lpSum(
                employee.shift_vars[day, work_type] for employee in self.employees for work_type in self.work_types
            )
            full_emp = pulp.lpSum(
                full_emp.shift_vars[day] for full_emp in self.full_time_employees
            )
            self.prob += temp_emp + full_emp >= self.absolute_min_workers_per_day + 1, f"Min_workers_day_{day}"

    # 作業タイプごとに最低限必要な従業員数の制約

    def add_constraint_for_minimum_workers_per_worktype(self):
        for day in self.days:
            for work_type in self.work_types:
                if work_type != self.sacrificed_work:
                    self.prob += pulp.lpSum(
                        employee.shift_vars[day, work_type] for employee in self.employees
                    ) >= 1

    # 有給の日数を設定する
    def add_constraint_for_no_work_on_paid_off(self):
        for employee in self.employees:
            self.prob += pulp.lpSum(
                employee.paid_vars[day] for day in self.days
            ) == employee.paid_off
            for day in self.days:
                self.prob += employee.assigned_vars[day] + employee.paid_vars[day] <= 1

    # 従業員ができる仕事のみを割り当てる制約
    def add_constraint_for_allowed_work_types(self):
        for employee in self.employees:
            for day in self.days:
                for work_type in self.work_types:
                    if work_type not in employee.work_type:
                        self.prob += employee.shift_vars[(day, work_type)] == 0

    def math_round(self, number, digits=0):
        if digits == 0:
            # 小数点以下の値が.5以上なら1を加えることで上に丸める
            if number >= 0:
                return math.floor(number + 0.5)
            else:
                return math.ceil(number - 0.5)

    # （完全週の）一週間当たりの業務数制限

    def add_constraint_for_weekly_working_days(self):
        first_sunday, days_in_month, weeks_in_month = self.caluculate_days()
        days_in_last_week = (days_in_month + 1) - ((first_sunday) + weeks_in_month * 7)
        for employee in self.employees:
            if days_in_last_week != 0:
                last_weekly_days = self.math_round(employee.weekly_days * days_in_last_week / 7)
                print(employee.name, "最終週勤務数", last_weekly_days)
            else:
                last_weekly_days = 0

            for week in range(weeks_in_month + 1):
                if week == weeks_in_month:
                    if days_in_last_week != 0:
                        start_day = first_sunday + week * 7
                        end_day = start_day + days_in_last_week
                        print("月末開始終了", start_day, end_day)
                        weekly_days_for_constraint = last_weekly_days
                    else:
                        break
                else:
                    start_day = first_sunday + week * 7
                    end_day = start_day + 7
                    weekly_days_for_constraint = employee.weekly_days

                if employee.over_work:
                    self.prob += pulp.lpSum(employee.shift_vars[(day, work_type)]
                                            for day in range(start_day, end_day) for
                                            work_type in self.work_types) >= weekly_days_for_constraint
                else:
                    self.prob += pulp.lpSum(employee.shift_vars[(day, work_type)]
                                            for day in range(start_day, end_day) for
                                            work_type in self.work_types) == weekly_days_for_constraint

    # 1日単位で出勤したかどうかを管理する変数assigned_varsを設定する制約を追加
    def add_constraint_for_daily_assignment(self):
        for employee in self.employees:
            for day in self.days:
                self.prob += employee.assigned_vars[day] >= pulp.lpSum(employee.shift_vars[(day, work_type)]
                                                                       for work_type in self.work_types) * (1 / len(self.work_types))

    # 5日連続の勤務禁止
    def add_constraint_for_no_consecutive_work_days(self):
        for employee in self.employees:
            for start_day in range(len(self.days) - 4):
                consecutive_days_work = pulp.lpSum(
                    employee.assigned_vars[day] for day in range(start_day, start_day + 5))
                paid_off = pulp.lpSum(employee.paid_vars[day] for day in range(start_day, start_day + 5))
                self.prob += consecutive_days_work + \
                    paid_off <= 4, f"no_consecutive_5_days_work_{employee.id}_{start_day}"

    # 全日勤務可能な従業員について、4日間連続で全日勤務は禁止
    def add_constraint_for_daily_workable_employee(self):
        for employee in self.employees:
            for start_day in range(len(self.days) - 3):
                self.prob += pulp.lpSum(employee.shift_vars[(day, work_type)]
                                        for day in range(start_day, start_day+4) for
                                        work_type in self.work_types) <= 7

    # 第三木曜日は全員出勤

    def add_constraint_for_all_employees_third_thursday_attendance(self):
        first_sunday, _, _ = self.caluculate_days()
        if first_sunday >= 3:
            the_third_Thursday = first_sunday + 11
        else:
            the_third_Thursday = first_sunday + 18

        print(the_third_Thursday)

        self.prob += pulp.lpSum(employee.shift_vars[(the_third_Thursday, self.work_types[0])]
                                for employee in self.employees) >= 2
        self.prob += pulp.lpSum(employee.shift_vars[(the_third_Thursday, self.work_types[1])]
                                for employee in self.employees) >= 2
        self.prob += pulp.lpSum(employee.shift_vars[(the_third_Thursday, self.work_types[2])]
                                for employee in self.employees) >= 2
        self.prob += pulp.lpSum(employee.shift_vars[(the_third_Thursday, self.work_types[3])]
                                for employee in self.employees) >= 1
        self.prob += pulp.lpSum(employee.shift_vars[(the_third_Thursday, self.work_types[4])]
                                for employee in self.employees) >= 1
        self.prob += pulp.lpSum(employee.shift_vars[(the_third_Thursday, self.work_types[5])]
                                for employee in self.employees) >= 1
        for employee in self.employees:
            self.prob += pulp.lpSum(employee.shift_vars[(the_third_Thursday, work_type)]
                                    for work_type in self.work_types) == 1

    def add_constraint_for_no_consecutive_work_3days(self):
        for employee in self.employees:
            if employee.id in [1, 2, 3, 4, 5]:
                for start_day in range(len(self.days) - 2):
                    consecutive_days_work = pulp.lpSum(
                        employee.assigned_vars[day] for day in range(start_day, start_day + 3))
                    paid_off = pulp.lpSum(employee.paid_vars[day] for day in range(start_day, start_day + 3))
                    self.prob += consecutive_days_work + \
                        paid_off <= 2, f"no_consecutive_3_days_work_{employee.id}_{start_day}"

    ########################
    # 個別の制約条件
    #########################

    def add_constraint_for_individual_employee(self):
        for employee in self.employees:
            # 従業員１
            if employee.id == 1:
                # 夕食の次の日昼食は嫌
                for start_day in range(len(self.days) - 1):
                    is_assigned_today_evning_work = pulp.lpSum(employee.shift_vars[(start_day, self.work_types[i])]
                                                               for i in range(3, 6))
                    is_assigned_tommorow_day_work = pulp.lpSum(employee.shift_vars[(start_day+1, self.work_types[i])]
                                                               for i in range(3))
                    self.prob += is_assigned_today_evning_work + is_assigned_tommorow_day_work <= 1

            # 従業員5
            if employee.id == 5:
                # 土日の休み
                holidays = []
                first_sunday, days_in_month, weeks_in_month = self.caluculate_days()
                for day in range(len(self.days)):
                    if day % 7 == (first_sunday+5) % 7:
                        holidays.append(day)
                    elif day % 7 == (first_sunday+6) % 7:
                        holidays.append(day)
                    else:
                        continue
                self.prob += pulp.lpSum(employee.assigned_vars[holiday]
                                        for holiday in holidays) <= len(holidays)-2, f"week_end_day_off_for_{employee.id}"

              # 従業員id5が夕２に入るとき、夕１には必ず従業員がいる
                for day in self.days:
                    self.prob += pulp.lpSum(employee.shift_vars[(day, self.work_types[4])]) <= pulp.lpSum(emp.shift_vars[(day, self.work_types[3])]
                                                                                                          for emp in self.employees)

    #######################
    # 先月分考慮
    #######################
    # 先月分のシフトを考慮した一週間当たりの業務数制限を設定する制約

    def add_constraint_for_weekly_working_days_informed_by_last_month_shift(self):
        first_sunday, _, _ = self.caluculate_days()
        print(first_sunday, "first")
        if first_sunday != 0:
            print("3月第一月曜日", first_sunday)
            for employee in self.employees:
                if not employee.over_work:
                    self.prob += (employee.weekly_days - employee.last_month_period_work_days - pulp.lpSum(employee.shift_vars[(day, work_type)]
                                                                                                           for day in range(first_sunday)
                                                                                                           for work_type in self.work_types))/7 <= employee.first_week_penalty_vars
                    self.prob += employee.weekly_days - employee.last_month_period_work_days >= pulp.lpSum(employee.shift_vars[(day, work_type)]
                                                                                                           for day in range(first_sunday)
                                                                                                           for work_type in self.work_types)

    # 先月分のシフトを考慮した5日連続の勤務を禁止する制約
    def add_constraint_for_no_consecutive_work_days_informed_by_last_month_shift(self):
        for employee in self.employees:
            consecutive_days_work = pulp.lpSum(employee.assigned_vars[day]
                                               for day in range(5 - employee.last_month_consecutive_days))
            paid_off = pulp.lpSum(employee.paid_vars[day] for day in range(5 - employee.last_month_consecutive_days))
            self.prob += consecutive_days_work + paid_off <= 4 - employee.last_month_consecutive_days

    # 先月のシフトを考慮した3日連続の勤務を禁止する制約
    def add_constraint_for_no_consecutive_work_3days_informed_by_last_month_shift(self):
        for employee in self.employees:
            if employee.id in [1, 2, 3, 4, 5]:
                consecutive_days_work = pulp.lpSum(employee.assigned_vars[day]
                                                   for day in range(3 - employee.last_month_consecutive_days))
                paid_off = pulp.lpSum(employee.paid_vars[day]
                                      for day in range(3 - employee.last_month_consecutive_days))
                self.prob += consecutive_days_work + paid_off <= 2 - employee.last_month_consecutive_days
    # 先月分を考慮した従業員の個別制約を追加

    def add_constraint_for_individual_employee_informed_by_last_month_shift(self):
        for employee in self.employees:
            # 従業員１
            if employee.id == 1:
                # 夕食の次の日昼食は嫌
                if employee.last_month_consecutive_days >= 1:
                    self.prob += employee.shift_vars[(0, self.work_types[1])] <= 0

    ############################
    # 常勤従業員に対する制約
    ###########################
    # 常勤従業員は特定の日に出勤するようにする制約

    def culuculate_must_work_days(self):
        first_sunday, _, _ = self.caluculate_days()
        must_work_days = []
        # 第一月曜日の時点で第一木金が終わっている
        if first_sunday >= 4:
            must_work_days.append(first_sunday - 4)
            must_work_days.append(first_sunday - 3)
            must_work_days.append(first_sunday + 4)
            must_work_days.append(first_sunday + 10)
        # 第一月曜日の時点で第一金のみが終わっている
        elif first_sunday == 3:
            must_work_days.append(first_sunday + 3)
            must_work_days.append(first_sunday - 3)
            must_work_days.append(first_sunday + 4)
            must_work_days.append(first_sunday + 17)
        else:
            must_work_days.append(first_sunday + 3)
            must_work_days.append(first_sunday + 4)
            must_work_days.append(first_sunday + 11)
            must_work_days.append(first_sunday + 17)
        print(must_work_days)
        return must_work_days

    # 第一木金、第二金、第三木曜出勤

    def add_constraint_for_work_day_for_full_time_emp(self):
        must_work_days = self.culuculate_must_work_days()
        for full_emp in self.full_time_employees:
            for day in must_work_days:
                self.prob += pulp.lpSum(full_emp.shift_vars[day]) == 1

    # 常勤従業員は月に指定された回数だけ休むようにする制約
    def add_constraint_for_holiday_count_for_full_time_emp(self):
        for full_emp in self.full_time_employees:
            self.prob += pulp.lpSum(full_emp.shift_vars[day]
                                    for day in self.days) == len(self.days) - full_emp.holiday_count_per_month

    # 常勤従業員に対して指定された回数の有給を与える制約
    def add_constraint_for_paid_off_for_full_time_emp(self):
        for full_emp in self.full_time_employees:
            self.prob += pulp.lpSum(
                full_emp.paid_vars[day] for day in self.days
            ) == full_emp.paid_off
            for day in self.days:
                self.prob += full_emp.shift_vars[day] + full_emp.paid_vars[day] <= 1

    # 常勤従業員に対して5連勤を禁止する制約
    def add_constraint_for_no_consecutive_work_days_for_full_time_emp(self):
        for full_emp in self.full_time_employees:
            for start_day in range(len(self.days) - 4):
                consecutive_days_work = pulp.lpSum(full_emp.shift_vars[day] for day in range(start_day, start_day + 5))
                paid_off = pulp.lpSum(full_emp.paid_vars[day] for day in range(start_day, start_day + 5))
                self.prob += consecutive_days_work + \
                    paid_off <= 4, f"no_consecutive_5_days_work_{full_emp.id}_{start_day}"

    # 常勤従業員に対して先月分のシフトを考慮して5日連続の勤務を禁止する制約
    def add_constraint_for_no_consecutive_work_days_informed_by_last_month_shift_for_full_time_emp(self):
        for full_emp in self.full_time_employees:
            consecutive_days_work = pulp.lpSum(full_emp.shift_vars[day]
                                               for day in range(5 - full_emp.last_month_consecutive_days))
            paid_off = pulp.lpSum(full_emp.paid_vars[day] for day in range(5 - full_emp.last_month_consecutive_days))
            self.prob += consecutive_days_work + paid_off <= 4 - full_emp.last_month_consecutive_days

    # 常勤従業員に対してシフト希望を守る制約
    def add_constraint_for_day_off_requests_for_full_time_emp(self):
        must_work_days = self.culuculate_must_work_days()
        for full_emp in self.full_time_employees:
            for day in full_emp.day_off_requests:
                if day not in must_work_days:
                    self.prob += full_emp.shift_vars[day] <= 0

    #######################
    # 結果の表示
    #######################

    def display_employees_schedule(self):
        schedule_df = self.create_employees_schedule()
        return schedule_df

    def create_employees_schedule(self):
        # 曜日データ
        num_days = calendar.monthrange(self.year, self.month)[1]
        dates = [datetime(self.year, self.month, day)
                 for day in range(1, num_days + 1)]
        weekdays_japanese = ['月', '火', '水', '木', '金', '土', '日']
        column_names = [date.day for date in dates]
        weekday_data = [weekdays_japanese[date.weekday()] for date in dates]
        df_weekday = pd.DataFrame([weekday_data], index=['曜日'], columns=column_names)

        # 従業員の勤務表
        day_labels = [day + 1 for day in self.days]
        employee_rows = []
        for e in self.employees:
            employee_rows.append(f"{e.name} - 業務1")
            employee_rows.append(f"{e.name} - 業務2")

        schedule_df = pd.DataFrame(index=employee_rows, columns=day_labels)

        # 各従業員のスケジュールをDataFrameに割り当て
        for employee in self.employees:
            for day in self.days:
                assigned_works = []  # 割り当てられた業務を保持するリスト
                for work_type in self.work_types:
                    if pulp.value(employee.shift_vars[day, work_type]) == 1:
                        assigned_works.append(work_type)

                if pulp.value(employee.paid_vars[day]) == 1:
                    schedule_df.at[f"{employee.name} - 業務1", day + 1] = "有休"
                elif day in employee.day_off_requests:
                    continue
                elif not assigned_works:
                    schedule_df.at[f"{employee.name} - 業務1", day + 1] = "／"
                for i, work in enumerate(assigned_works):
                    schedule_df.at[f"{employee.name} - 業務{i+1}", day + 1] = work

        schedule_df = schedule_df.replace(
            {'day': '昼', 'evening': '夕'}, regex=True)

        schedule_df.loc['二人体制の日'] = np.nan
        schedule_df.loc[""] = np.nan

        for column in schedule_df.columns:
            if '夕1' not in schedule_df[column].values:
                schedule_df.at['二人体制の日', column] = '夕1'

        for e in self.full_time_employees:
            schedule_df.loc[f"{e.name} - 業務1"] = np.nan
            schedule_df.loc[f"{e.name} - 業務2"] = np.nan
            for day in self.days:
                if pulp.value(e.paid_vars[day]) == 1:
                    schedule_df.at[f"{e.name} - 業務1", day + 1] = "有休"
                elif pulp.value(e.shift_vars[day]) == 0:
                    schedule_df.at[f"{e.name} - 業務1", day + 1] = "／"

        shift_df = pd.concat([df_weekday, schedule_df], ignore_index=False)

        return shift_df

    def replace_text(self, text):
        match = re.match(r'day(\d+)', text)
        if match:
            return f'昼{match.group(1)}'
        match = re.match(r'evening(\d+)', text)
        if match:
            return f'夕{match.group(1)}'
        return text

    #######################
    # 実行
    #######################

    def solve(self):
        self.create_variables()
        self.set_objective()
        self.add_constraints()
        self.prob.solve()
        solution_status = pulp.LpStatus[self.prob.status]

        if solution_status == 'Optimal':
            schedule_df = self.display_employees_schedule()
            return schedule_df
        else:
            return json.dumps({"message": "No optimal solution found."}, ensure_ascii=False)
