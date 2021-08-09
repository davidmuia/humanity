# Dockerfile, Image, Container
FROM python:3.9

ADD app.py .

WORKDIR /humanity_app

COPY requirements.txt .

RUN pip install -r requirements.txt

CMD [ "python", "./app.py" ]