FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
COPY .gitignore .
COPY .streamlit .streamlit

RUN apt-get update && \
    apt-get -y upgrade && \
    pip install -r requirements.txt

EXPOSE 8501

ENTRYPOINT ["streamlit", "run"]

CMD ["src/app.py"]