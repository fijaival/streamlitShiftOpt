import streamlit as st
from .create_excel import create_excel


def download(df):
    buf = create_excel(df)

    # Streamlitのダウンロードボタンを作成
    st.download_button(
        "Download",
        buf.getvalue(),
        "shift.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
