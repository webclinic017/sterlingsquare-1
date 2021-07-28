FROM python:3

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app


COPY req_ubuntu.txt .




RUN pip3 install -r req_ubuntu.txt

RUN pip3 install pandas-datareader --upgrade