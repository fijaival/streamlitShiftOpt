import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_preprocessor import process_data
from utils.download import download
from utils.validate_input import validate_input
from run_optimization import run_optimization
from auth import check_password

def main():
    st.title('シフト自動生成')
    # 現在の年を取得
    current_year = datetime.now().year
    years = ['年を選択してください'] + \
        list(range(current_year, current_year + 2))  # プレースホルダーを追加
    selected_year = st.selectbox('年を選択してください', years)

    months = ['月を選択してください'] + list(range(1, 13))  # プレースホルダーを追加
    selected_month = st.selectbox('月を選択してください', months)

    # ユーザーが年と月を明示的に選択するまでアップロードをブロック
    if selected_year != '年を選択してください' and selected_month != '月を選択してください':
        uploaded_file = st.file_uploader(
            "Excelファイルをアップロードしてください", type=["xlsx"])
        if uploaded_file is not None:
            isVaild, msg = validate_input(
                uploaded_file, selected_year, selected_month)
            if isVaild:
                employees_data, full_time_employees_data = process_data(
                    uploaded_file, selected_year, selected_month)
                if employees_data and full_time_employees_data:
                    result = run_optimization(
                        employees_data, full_time_employees_data, selected_year, selected_month)
                    if isinstance(result, pd.DataFrame):
                        st.write("## スケジュール結果")
                        st.dataframe(result, 1600, 500)
                        download(result)
                    else:
                        st.write("シフトの作成に失敗しました")
            else:
                st.error(msg)


if __name__ == "__main__":
    if not check_password():
        st.stop()  # Do not continue if check_password is not True.
    main()
