from typing import List

import report_app.report_logic.mounter as mtr
import report_app.report_logic.report_carrier as rpc

from report_app.report_logic.custom_errors import *


def magic_away_from_Hogwarts(
        sql_title: str,
        sql_query: str,
        db_server: str,
        file_format: str,
        recipients: List[str],
        carbon_copy: List[str] = None,
) -> None:
    """
    Создать отчёт и отправить письмо.

    :param sql_title: название файла (с расширением .sql)
    :param sql_query: текст sql-запроса, полученный из формы для редактирования
    :param db_server: сервер, на котором будет выполнен sql-запрос
    :param file_format: формат файла с отчётом (поддерживаются xlsx и csv)
    :param recipients: список почтовых адресов получателей отчёта
    :param carbon_copy: почтовый адрес в копию
    :return: None
    """

    if file_format not in ('xlsx', 'csv'):
        raise FileFormatError(f"указанный формат {file_format} отчёта не поддерживается, доступны xlsx и csv")

    # Создание уникального названия файла
    abs_file_path = rpc.get_unique_title(
        report_title=sql_title,
        file_format=file_format
    )

    # Сохранение выгрузки в файл
    is_format_changed = False
    if mtr.is_mount_ready():
        is_format_changed = rpc.prepare_report_file(db_server, sql_query, abs_file_path, file_format=file_format)
        if is_format_changed:
            abs_file_path = abs_file_path[:-4] + 'csv'

    # Отправка письма
    rpc.send_email(recipients, abs_file_path, is_format_changed, carbon_copy=carbon_copy)
