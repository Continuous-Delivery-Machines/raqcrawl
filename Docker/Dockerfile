FROM python:3.6
MAINTAINER wenzel@th-brandenburg.de

ENV RAQ_CRAWLER_STAGE PROD

COPY requirements.txt /app/install/requirements.txt
RUN pip install -r /app/install/requirements.txt

COPY raqc/ /app/raq-crawler/

CMD python /app/raq-crawler/main.py ${RAQ_CRAWLER_STAGE}