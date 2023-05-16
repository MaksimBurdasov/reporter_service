import os

import smtplib
from email.message import EmailMessage

from pathlib import Path
from os.path import exists

import pandas as pd
import openpyxl as ox
from sqlalchemy import create_engine, text

from typing import List, Iterator

from datetime import datetime

import logging
from report_app.report_logic.custom_decorators import custom_logging_decorator

from report_app.report_logic.database_manipulator import prepare_connection_url


logger = logging.getLogger(__name__)

# Адрес, от имени которого будет произведена отправка письма
FAKE_ADDRESS = (
    'no-reply@alfabank.ru',  # 0
    'rc_report_box@alfabank.ru',  # 1
    'support_rc@alfabank.ru',  # 2
    'MBurdasov@alfabank.ru',  # 3
)[2]

MAIL_CLIENT_PORT = 25  # порт, предназначенный для почтового клиента

# Адрес в копии по умолчанию
DEFAULT_CARBON_COPY = "support_rc@alfabank.ru"

DEFAULT_REPORTS_FOLDER = "\\\\bpdb1\\shar_all\\ReporterDepot\\"
CONTAINER_FOLDER = "/mnt/ReporterDepot"

OPTIMAL_CHUNKSIZE = 200000
MAX_XL_ROWS = 400000

WIN_ENCODING = 'utf-8'


@custom_logging_decorator(logger)
def get_unique_title(report_title: str,
                     file_format: str,
                     dir_path: str = CONTAINER_FOLDER) -> str:
    """
    Получить уникальное название файла с указанием времени создания.
    Вернуть абсолютный адрес файла.

    :param report_title: название отчёта
    :param file_format: формат отчёта
    :param dir_path: путь папки хранения файла
    :return:
    """

    if report_title[-4:] == '.sql':
        report_title = report_title[:-4]

    date_stamp = datetime.now().strftime("%y%m%d")
    unique_title = f'{report_title}_{date_stamp}.{file_format}'

    if not exists(dir_path + '/' + unique_title):
        unique_title = dir_path + '/' + unique_title
        logger.warning("сформировано уникальное название: " + unique_title)
        return unique_title

    version = 1
    while True:
        unique_title = f'{report_title}_{date_stamp}({version}).{file_format}'
        if not exists(dir_path + '/' + unique_title):
            unique_title = dir_path + '/' + unique_title
            logger.warning("сформировано уникальное название: " + unique_title)
            return unique_title
        version += 1


# ----------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------- Сохранение отчета в файл ----------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# @custom_logging_decorator(logger)
# def _update_spreadsheet(path: str,
#                         df: pd.DataFrame,
#                         star_col: int,
#                         start_row: int,
#                         sheet_name: str = "Sheet1") -> None:
#     """
#     Произвести дозапись данных в существующий Excel-файл с сохранением форматирования
#
#     :param path: путь до файла Excel
#     :param df: датафрейм Pandas для записи
#     :param star_col: стартовая колонка в таблице листа Excel, куда будут писаться данные
#     :param start_row: стартовая строка в таблице листа Excel, куда будут писаться данные
#     :param sheet_name: название листа в таблице Excel, куда будут писаться данные
#     """
#
#     wb = ox.load_workbook(path)  # <- проблема тут
#
#     for row in range(0, len(df)):
#         for col in range(0, len(df.iloc[row])):
#             wb[sheet_name].cell(start_row + row, star_col + col).value = df.iloc[row][col]
#
#     wb.save(path)


# @custom_logging_decorator(logger)
# def _make_xl_out_of_iterator(chunks_iterator: Iterator[pd.DataFrame],
#                              path: str) -> None:
#     """
#     Создать Excel-файл с отчетом.
#
#     :param chunks_iterator: итератор (курсор) по базе данных
#     :param path: абсолютный путь, по которому будет сохранен файл
#     """
#
#     with pd.ExcelWriter(path, engine="openpyxl", mode='w') as writer:
#         chunk = next(chunks_iterator)
#         chunk.to_excel(writer, index=False, engine='openpyxl', encoding=WIN_ENCODING)
#         # первую строку займут заголовки
#         # строка len(chunk) + 1 будет последней непустой
#         # строка len(chunk) + 2 будет первой свободной для записи
#         first_empty_line = chunk.shape[0] + 2
#
#     logger.warning("создан файл Excel")
#
#     for chunk in chunks_iterator:
#         logger.warning(f"в Excel-файл записано: {first_empty_line-1} строк")
#         _update_spreadsheet(path, chunk, star_col=1, start_row=first_empty_line)
#         first_empty_line += chunk.shape[0]


@custom_logging_decorator(logger)
def _make_xl_out_of_dataframe(dataframe: pd.DataFrame,
                              path: str) -> None:
    """
    Создать Excel-файл с отчетом.

    :param dataframe: выгрузка из БД
    :param path: абсолютный путь, по которому будет сохранен файл
    """

    with pd.ExcelWriter(path, engine="openpyxl", mode='w') as writer:
        dataframe.to_excel(writer, index=False, engine='openpyxl', encoding=WIN_ENCODING)


@custom_logging_decorator(logger)
def _make_csv_out_of_iterator(chunks_iterator: Iterator[pd.DataFrame],
                              path: str) -> None:
    """
    Создать CSV-файл с отчетом.

    :param chunks_iterator: итератор (курсор) по базе данных
    :param path: абсолютный путь, по которому будет сохранен файл
    """

    with open(path, 'w', newline='') as f_out:
        # Запись первого чанка с названием столбцов
        next(chunks_iterator).to_csv(f_out, index=False, encoding=WIN_ENCODING)

        for chunk in chunks_iterator:
            chunk.to_csv(f_out, index=False, header=False, encoding=WIN_ENCODING)  # названия столбцов не пишутся


@custom_logging_decorator(logger)
def prepare_report_file(server: str,
                        sql_query: str,
                        absolute_path: str,
                        file_format: str = 'xlsx',
                        ) -> bool:
    """
    Создать и сохранить файл в примонтированную папку.

    :param server: название сервера с БД
    :param sql_query: текст запроса, полученный из формы на сайте
    :param absolute_path: полный адрес, по которому должен быть сохранен файл
    :param file_format: формат файла ('xlsx' или 'csv')
    :return: был ли изменен формат отчета из-за его большого объема
    """
    sql_query = text(sql_query)

    conn_url = prepare_connection_url(host=server)
    engine = create_engine(conn_url)

    # Приблизительный подсчет количества строк в отчете с округлением к большему
    with engine.connect().execution_options(stream_results=True) as conn:
        chunks_iter = pd.read_sql(sql_query, conn, chunksize=OPTIMAL_CHUNKSIZE)
        approx_rows_number = sum(1 for _ in chunks_iter) * OPTIMAL_CHUNKSIZE
    logger.warning(f"отчет содержит от {approx_rows_number - OPTIMAL_CHUNKSIZE} до {approx_rows_number} строк")

    is_format_changed = False
    if file_format == 'xlsx' and approx_rows_number > OPTIMAL_CHUNKSIZE:
        file_format = 'csv'
        absolute_path = absolute_path[:-4] + 'csv'
        is_format_changed = True

    with engine.connect().execution_options(stream_results=True) as conn:

        if file_format == 'xlsx':
            df = pd.read_sql(sql_query, conn)
            _make_xl_out_of_dataframe(df, absolute_path)
        elif file_format == 'csv':
            chunks_iter = pd.read_sql(sql_query, conn, chunksize=OPTIMAL_CHUNKSIZE)
            _make_csv_out_of_iterator(chunks_iter, absolute_path)

    return is_format_changed


# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


# ----------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------- Отправка писем ---------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
@custom_logging_decorator(logger)
def get_email_template(report_title: str,
                       is_format_changed: bool,
                       suitable_for_email: bool) -> str:
    """
    Пучить текст шаблона для письма.

    :param report_title: название файла (с расширением)
    :param is_format_changed: был ли формат отчета принудительно изменен
    :param suitable_for_email: подходит ли размер файла для отправки почтой (меньше либо равен 20 Мб)
    :return: текст с разметкой html
    """

    format_issue = ""
    if is_format_changed:
        format_issue = (
            "Результат содержит большое количество записей.<br>"
            "Формат изменён на <b>CSV</b> для упрощения выгрузки.<br>"
        )

    how_to_find_a_report = "<tt><i>см. приложение к письму</i></tt><br>"
    if not suitable_for_email:
        how_to_find_a_report = (
            "<br>"
            "Превышен разрешённый для отправки почтой вес файла.<br>"
            r"Отчёт будет выложен в сетвую папку: \\bpdb1\shar_all\ReporterDepot<br>"
        )

    how_to_export_csv = ""
    if report_title[-4:] == '.csv':
        how_to_export_csv = (
            "<tt><i>Для корректного отображения кириллицы при экспорте CSV -> Excel используйте кодировку <b>Юникод (UTF-8)</b></i></tt><br>"
            "<br>"
        )

    final_message = (
        "Добрый день.<br>"
        "<br>"
        "Отчёт готов.<br>"
        f"{format_issue}"
        f"Файл: {report_title}<br>"
        f"{how_to_find_a_report}"
        "<br>"
        f"{how_to_export_csv}"
        "--<br>"
        "Отдел технической экспертизы систем корпоративного и транзакционного бизнеса"
    )

    return final_message


@custom_logging_decorator(logger)
def send_email(recipients: List[str],
               attachment: str,
               is_format_changed: bool,
               carbon_copy: List[str] = None) -> None:
    """
    Отправить письмо на почту.

    :param recipients: получатели
    :param attachment: абсолютный путь до отчета (в контейнере)
    :param is_format_changed: менялся ли формат файла на CSV принудительно
    :param carbon_copy: адреса в копию
    """

    msg = EmailMessage()
    msg['Subject'] = "Выгрузка по заявке '02.08.Отчетность'"
    msg['From'] = FAKE_ADDRESS
    msg['To'] = ' ,'.join(recipients)
    if carbon_copy is None:
        msg['Cc'] = DEFAULT_CARBON_COPY
    else:
        msg['Cc'] = ' ,'.join(carbon_copy)

    # int(os.path.getsize(attachment) / 1048576) + 1 - это размер файла, Мб (с запасом)
    suitable_for_email = (int(os.path.getsize(attachment) / 1048576) + 1) <= 20

    # Добавление текста
    mail_text = get_email_template(attachment.split('/')[-1], is_format_changed, suitable_for_email)
    msg.set_content(mail_text, subtype="HTML")  # subtype - параметр парсинга

    if suitable_for_email:
        with open(attachment, 'rb') as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype=attachment.split('.')[-1],  # формат отчёта
                filename=attachment.split('/')[-1]  # имя файла
            )
        os.remove(attachment)  # удаление файла, если он успешно прикрепился к письму

    # Отправка письма
    with smtplib.SMTP('gw.alfaintra.net', MAIL_CLIENT_PORT) as smtp:
        smtp.send_message(msg)

    logger.warning('письмо успешно отправлено на почту')
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
