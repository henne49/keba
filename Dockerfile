# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY keba_export.py keba_export.py
COPY template.json c-keba.json

CMD ["python3", "keba_export.py"]