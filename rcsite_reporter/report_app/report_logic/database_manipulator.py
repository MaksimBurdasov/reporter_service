import pyodbc
from sqlalchemy.engine import URL
from sqlalchemy import create_engine, text

import pandas as pd

from typing import List

import logging
from report_app.report_logic.custom_decorators import custom_logging_decorator

import report_app.report_logic.config as cn
from report_app.report_logic.custom_errors import DBWorkError

logger = logging.getLogger(__name__)

RC_HOST = "OSSKTBAPP1"
LOG_DB = "RCSITE"


@custom_logging_decorator(logger)
def prepare_connection_url(host: str, db: str = 'master') -> URL:
    """Подготовить объект класса sqlalchemy.engine.URL для подключения к базе данных."""
    # sqlalchemy.engine.URL template: dialect+driver://username:password@host:port/database?<params>
    url_object = URL.create(
        drivername="mssql+pyodbc",
        username=cn.get_db_user(),
        password=cn.get_db_pass(),
        host=host,
        port=1433,  # наш SQL-сервер обрабатывает запросы на этом порту
        database=db,
        # query={"driver": "ODBC Driver 13 for SQL Server"}
        query={"driver": pyodbc.drivers()[-1]}
    )
    return url_object


def prepare_pyodbc_connection_string(host: str, db: str = 'master') -> str:
    """Сформировать строку подключения к БД."""
    connection_string = 'DRIVER={' + pyodbc.drivers()[-1] + '};' + \
                        f'Server={host};' + \
                        f'Database={db};' + \
                        'UID=' + cn.get_db_user() + ';' + \
                        'PWD=' + cn.get_db_pass() + ';' + \
                        'encrypt=no'
    return connection_string


def get_servers_info() -> List[dict]:
    """Вернуть информацию по серверам из таблицы RCSITE.dbo.ReporterHostInfo (OSSKTBAPP1)."""
    engine = create_engine(prepare_connection_url("OSSKTBAPP1", "RCSITE"))
    with engine.connect() as cnxn:
        sql_text = text("SELECT sName, sDescription FROM RCSITE.dbo.ReporterHostInfo;")
        df = pd.read_sql_query(sql_text, cnxn)
        return [{'name': pair[0], 'description': pair[1]} for pair in df.values]


# !!! Не указывать здесь декоратор логгирования, иначе возникает бесконечная рекурсия
def note_log(level: str, logger_name: str, log_message: str, error_traceback: str) -> None:
    """Записать лог в базу данных."""

    sql_query = """
        INSERT INTO RCSITE.dbo.MaxLogs (
            sProject,
            sLogLevel,
            sLoggerName,
            sLogMessage,
            sErrorTraceback
        )
        VALUES (
            ?,  --project
            ?,  --log level
            ?,  --logger name
            ?,  --log message
            ?   --error traceback
        )
    """

    cn_str = prepare_pyodbc_connection_string(host=RC_HOST, db=LOG_DB)
    try:
        with pyodbc.connect(cn_str, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_query, ("RC Reporter", level, logger_name, log_message, error_traceback))
                cursor.commit()
    except Exception as error:
        raise DBWorkError(format(error))
