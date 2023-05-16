import pandas as pd

import pyodbc
from sqlalchemy.engine import URL
from sqlalchemy import create_engine, text

import os

from time import perf_counter_ns

import openpyxl

from typing import Iterator

import logging

import report_app.report_logic.config as cn


logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)

XL_REPORT_PATH = r"\\bpdb1\shar_all\ReporterDepot\report.xlsx"
CSV_REPORT_PATH = r"\\bpdb1\shar_all\ReporterDepot\report.csv"


def time_of_function(function):
    def wrapper(*args, **kwargs):
        start_time = perf_counter_ns()
        res = function(*args, **kwargs)
        exec_time = perf_counter_ns() - start_time
        print(f"Время выполнения {function.__name__}: {exec_time / 10 ** 9}")
        return res
    return wrapper


def prepare_connection_url(host: str, db: str = 'master') -> URL:
    """Подготовить объект класса sqlalchemy.engine.URL для подключения к базе данных."""
    # sqlalchemy.engine.URL template: dialect+driver://username:password@host:port/database?<params>
    url_object = URL.create(
        drivername="mssql+pyodbc",
        username=cn.get_db_user(),
        password=cn.get_db_pass(),
        host=host,
        port=1433,
        database=db,
        query={"driver": pyodbc.drivers()[-1]}
    )
    return url_object


@time_of_function
def _update_spreadsheet(path: str, df, starcol: int = 1, startrow: int = 1, sheet_name: str = "Sheet1"):
    """
    Произвести дозапись данных в Excel-файл с сохранением форматирования

    :param path: путь до файла Excel
    :param df: датафрейм Pandas для записи
    :param starcol: стартовая колонка в таблице листа Excel, куда будут писаться данные
    :param startrow: стартовая строка в таблице листа Excel, куда будут писаться данные
    :param sheet_name: название листа в таблице Excel, куда будут писаться данные
    :return:
    """

    if not os.path.exists(path):
        with pd.ExcelWriter(path, engine="openpyxl", mode='w') as writer:
            df.to_excel(writer, index=False, engine='openpyxl')

    else:
        wb = openpyxl.load_workbook(path)
        for row in range(0, len(df)):
            for col in range(0, len(df.iloc[row])):
                wb[sheet_name].cell(startrow + row, starcol + col).value = df.iloc[row][col]

        wb.save(path)


@time_of_function
def _make_xl_out_of_iterator(chunks_iterator: Iterator[pd.DataFrame], path: str) -> None:
    with pd.ExcelWriter(path, engine="openpyxl", mode='w') as writer:
        chunk = next(chunks_iterator)
        chunk.to_excel(writer, index=False, engine='openpyxl')
        # первую строку займут заголовки
        # строка len(chunk) + 1 будет последней непустой
        # строка len(chunk) + 2 будет первой свободной для записи
        first_empty_line = chunk.shape[0] + 2

    sheet_name = "Sheet1"
    for chunk in chunks_iterator:
        if first_empty_line > 1000000:
            sheet_name = sheet_name[:5] + str(int(sheet_name[5:]) + 1)
        _update_spreadsheet(path, chunk, starcol=1, startrow=first_empty_line, sheet_name=sheet_name)
        first_empty_line += chunk.shape[0]


@time_of_function
def _make_csv_out_of_iterator(chunks_iterator: Iterator[pd.DataFrame], path: str) -> None:
    with open(path, 'w', newline='') as f_out:
        next(chunks_iterator).to_csv(f_out, index=False)  # запись первого чанка с названием столбцов

        for chunk in chunks_iterator:
            chunk.to_csv(f_out, index=False, header=False)  # пропускаем запись названий столбцов


@time_of_function
def prepare_report_file(sql_query: text, absolute_path: str = XL_REPORT_PATH, file_format: str = 'xlsx'):
    connection_url = prepare_connection_url(host='rcdb-reader')

    engine = create_engine(connection_url)
    with engine.connect().execution_options(stream_results=True) as conn:
        chunks_iter = pd.read_sql(sql_query, conn, chunksize=200000)

        if file_format == 'xlsx':
            _make_xl_out_of_iterator(chunks_iter, absolute_path)
        elif file_format == 'csv':
            _make_csv_out_of_iterator(chunks_iter, absolute_path)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


cn_url = prepare_connection_url(host='rcdb-listener')

sql_hard = text("""
SELECT
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета'
FROM LM1.dbo.vftSimpleRequest_listALL sr (NOLOCK)
	LEFT JOIN LM1.dbo.ftSimpleRequestProperty srp (NOLOCK) ON srp.idObject=sr.idSimpleRequest AND srp.idFieldType=480564
	LEFT JOIN LM1.dbo.ftSimpleRequestProperty srp2 (NOLOCK) ON srp2.idObject=sr.idSimpleRequest AND srp2.idFieldType=487569
	JOIN CB_CREDITCONVEYOR.dbo.CREDITREQUESTS cr ON cr.LMDealState=sr.idSimpleRequest
	JOIN CB_CREDITCONVEYOR.dbo.LOG L WITH (NOLOCK) ON L.RequestID = cr.RequestId
	JOIN CB_CREDITCONVEYOR.dbo.ROLES R WITH (NOLOCK) ON R.RoleID = L.RoleID
	JOIN CB_CREDITCONVEYOR.dbo.STATUSES D WITH (NOLOCK) ON L.FinalStatusID = D.ID
	JOIN CB_CREDITCONVEYOR.dbo.Users U WITH (NOLOCK) ON U.ID=l.UserID
WHERE 1=1
	AND sr.idSimpleRequestDocType=480562
	AND cr.CreationDateTime BETWEEN GETDATE() - 60 AND GETDATE()
ORDER BY sr.idSimpleRequest""")
sql_hard2 = text("""
SELECT
    sr.idSimpleRequest as ID,
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета',
	srp.sValue AS 'Причина закрытия счета'
FROM LM1.dbo.vftSimpleRequest_listALL sr (NOLOCK)
	LEFT JOIN LM1.dbo.ftSimpleRequestProperty srp (NOLOCK) ON srp.idObject=sr.idSimpleRequest AND srp.idFieldType=480564
	LEFT JOIN LM1.dbo.ftSimpleRequestProperty srp2 (NOLOCK) ON srp2.idObject=sr.idSimpleRequest AND srp2.idFieldType=487569
	JOIN CB_CREDITCONVEYOR.dbo.CREDITREQUESTS cr ON cr.LMDealState=sr.idSimpleRequest
	JOIN CB_CREDITCONVEYOR.dbo.LOG L WITH (NOLOCK) ON L.RequestID = cr.RequestId
	JOIN CB_CREDITCONVEYOR.dbo.ROLES R WITH (NOLOCK) ON R.RoleID = L.RoleID
	JOIN CB_CREDITCONVEYOR.dbo.STATUSES D WITH (NOLOCK) ON L.FinalStatusID = D.ID
	JOIN CB_CREDITCONVEYOR.dbo.Users U WITH (NOLOCK) ON U.ID=l.UserID
WHERE 1=1
	AND sr.idSimpleRequestDocType=480562
	AND cr.CreationDateTime BETWEEN GETDATE() - 60 AND GETDATE()
ORDER BY sr.idSimpleRequest
OFFSET :skip_rows ROWS FETCH NEXT :batch_size ROWS ONLY""")

sql_norm = text("""SELECT TOP 200001 
    srp2.sValue AS 'Источник поступления',
	CONVERT(NVARCHAR, cr.CreationDateTime, 20) AS 'Дата время создания заявки', sr.idSimpleRequest AS '№ Заявки', 
	srp.sValue AS 'Причина закрытия счета',
	sr.sPinEq AS 'ПИН Клиента по заявке', d.Name as 'Статус по заявке', CONVERT(NVARCHAR, l.ActionDateTime, 20) AS 'Дата время изменения статуса',
	CASE WHEN u.NAME LIKE '%Технич%' THEN 'Sistem' WHEN u.NAME='Technical_KK_sys' THEN 'Sistem' ELSE u.NAME end AS 'Пользователь изменивший статус ФИО пользователя', 
	CASE WHEN u.NAME LIKE '%Технич%' THEN 'Sistem' WHEN u.NAME='Technical_KK_sys' THEN 'Sistem' ELSE u.WindowsLogin end AS 'Пользователь изменивший статус ФИО пользователя',
	CASE WHEN l.FinalStatusID in (6659, 6657) THEN '+' ELSE '' end as 'Маркер финального статуса по заявке',
	CASE WHEN l.FinalStatusID in (6661, 6663) THEN '++' ELSE '' end as 'Маркер статуса на удержании по заявке'
FROM LM1..vftSimpleRequest_listALL sr (NOLOCK)
	left JOIN lm1..ftSimpleRequestProperty srp (NOLOCK) ON srp.idObject=sr.idSimpleRequest AND srp.idFieldType=480564
	left JOIN lm1..ftSimpleRequestProperty srp2 (NOLOCK) ON srp2.idObject=sr.idSimpleRequest AND srp2.idFieldType=487569
	JOIN CB_CREDITCONVEYOR..CREDITREQUESTS cr ON cr.LMDealState=sr.idSimpleRequest
	JOIN CB_CREDITCONVEYOR.dbo.LOG L WITH (NOLOCK) ON L.RequestID = cr.RequestId
	JOIN CB_CREDITCONVEYOR.dbo.ACTIONS A WITH (NOLOCK) ON A.ID= L.ActionID
	JOIN CB_CREDITCONVEYOR.dbo.ROLES R WITH (NOLOCK) ON R.RoleID = L.RoleID
	join CB_CREDITCONVEYOR.dbo.STATUSES D WITH (NOLOCK) ON L.FinalStatusID = D.ID
	join CB_CREDITCONVEYOR.dbo.Users U WITH (NOLOCK) ON U.ID=l.UserID
WHERE 1=1
	AND cr.CreationDateTime BETWEEN '2021-12-01' AND CAST(GETDATE() + 1 As Date)
	AND sr.idSimpleRequestDocType=480562
ORDER BY sr.idSimpleRequest""")


# prepare_report_file(sql, absolute_path=XL_REPORT_PATH, file_format='xlsx')
prepare_report_file(sql_norm, absolute_path=XL_REPORT_PATH, file_format='xlsx')
