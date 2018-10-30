FROM python:3.6-stretch

COPY requirements-pip.txt /tmp/
RUN pip install --requirement /tmp/requirements-pip.txt

RUN apt-get update && apt-get install -y \
        git
