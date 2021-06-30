FROM ubuntu:18.04

RUN apt-get update && \
    apt-get install --no-install-recommends -y python3.8 python3-pip python3.8-dev && \
    apt-get -y install vim && \
    apt-get -y install git &&\
    apt-get -y install python3-setuptools


ENV PYTHONBUFFERED 1

RUN mkdir /code

WORKDIR /code

COPY req_ubuntu.txt /code/


RUN apt-get -y install build-essential libssl-dev libffi-dev \
    python3-dev cargo


# RUN apk add --no-cache --update \
#     python3 python3-dev gcc \
#     gfortran musl-dev g++ \
#     libffi-dev openssl-dev cargo \
#     libxml2 libxml2-dev \
#     libxslt libxslt-dev \
#     libjpeg-turbo-dev zlib-dev

RUN apt install python3-pip

#RUN pip install --upgrade pip

RUN pip3 install setuptools_rust

RUN pip3 install cryptography



RUN pip3 install -r req_ubuntu.txt

COPY . /code/
