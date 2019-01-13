FROM python:3.6
MAINTAINER marvinlukas.wenzel@th-brandenburg.de

COPY resources/ /install_app

RUN pip install /install_app/app.tar.gz
CMD python