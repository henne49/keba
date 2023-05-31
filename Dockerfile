# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ADD static static
ADD templates templates
COPY app.py app.py
COPY template.json template.json

RUN mkdir data
VOLUME data

CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0", "--debug"]
