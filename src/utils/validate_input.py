import streamlit as st
import pandas as pd
import calendar


def validate_input(uploaded_file, year, month):
    with pd.ExcelFile(uploaded_file) as xls:
        # シート名のリストを取得
        sheet_names = xls.sheet_names

        # 期待するシート名
        expected_sheet_names = ['シフト希望', '非常勤', '常勤']

        # シート名が期待通りかどうかを検証
        if sheet_names[:3] == expected_sheet_names:
            return validate_shift_request(xls, 'シフト希望', year, month)
        else:
            return False, "シート名を正しく設定してください"


def validate_shift_request(xls, sheet_name, year, month):
    df = xls.parse(sheet_name)
    actual_days = df.shape[1] - 2

    days_in_month = calendar.monthrange(year, month)[1]
    if actual_days == days_in_month:
        return True, ""
    else:
        return False, "「シフト希望」シートの日数が作成したい月の日数と一致しません"
