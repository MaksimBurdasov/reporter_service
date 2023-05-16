# Ссылка на образ: https://hub.docker.com/r/cymagix/python-for-pyodbc-sqlserver
FROM docker-hub.binary.alfabank.ru/cymagix/python-for-pyodbc-sqlserver


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./openssl.cnf /etc/ssl/openssl.cnf

EXPOSE 8080

# Файл sources.list взят из статьи: http://confluence.moscow.alfaintra.net/pages/viewpage.action?pageId=609247812
COPY ./sources.list /etc/apt/sources.list
RUN apt-get update && apt-get install -y cifs-utils

RUN mkdir /mnt/ReporterDepot


COPY ./rcsite_reporter /rcsite_reporter

WORKDIR /rcsite_reporter

COPY ./pip.conf ./pip.conf
ENV PIP_CONFIG_FILE pip.conf

COPY ./requirements.txt ./requirements.txt
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN python -m pip install --requirement requirements.txt


CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
