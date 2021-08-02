FROM python:3

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

COPY requirements_ak.txt .

RUN pip3 install -r requirements_ak.txt

RUN pip3 install pandas-datareader --upgrade
