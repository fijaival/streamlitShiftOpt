from datetime import datetime, timedelta


def caluculate_third_thursday(year, month):
    first_day = datetime(year, month, 1)
    # 最初の日の曜日を取得 (月曜日が0、日曜日が6)
    first_day_weekday = first_day.weekday()
    # 第一木曜日までの日数を計算
    days_until_first_thursday = (3 - first_day_weekday) % 7
    first_thursday = first_day + timedelta(days=days_until_first_thursday)
    third_thursday = first_thursday + timedelta(days=14)
    return third_thursday.day
