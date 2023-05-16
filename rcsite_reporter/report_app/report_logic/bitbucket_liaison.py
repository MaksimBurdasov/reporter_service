import requests
from re import fullmatch

import logging
from report_app.report_logic.custom_decorators import custom_logging_decorator

import report_app.report_logic.config as cn

from report_app.report_logic.custom_errors import BitBucketWorkError


logger = logging.getLogger(__name__)

OSSKTB_PROJECT_URL = 'https://git.moscow.alfaintra.net/rest/api/1.0/projects/OSSKTB/repos/'


@custom_logging_decorator(logger)
def get_folders_list(url: str = OSSKTB_PROJECT_URL, limit: int = 1000):
    """Получить список словарей с информацией о папках, в которых хранятся SQL-запросы."""
    url = url + f'?limit={limit}'
    response = requests.get(
        url,
        auth=(
            cn.get_bitbucket_username(),
            cn.get_bitbucket_password()
        ),
        verify=False
    )

    dir_titles = []
    for folder in response.json()['values']:
        pattern = r'.+-reports?\b'
        # если название папки заканчивается на -reports или -report
        if fullmatch(pattern, folder['slug']):
            dir_titles.append({
                "name": folder['name'],
                "description": folder['description']
            })

    return dir_titles


@custom_logging_decorator(logger)
def get_files_list(slug: str, url: str = OSSKTB_PROJECT_URL, limit: int = 100):
    """Получить список с информацией по файлам с sql-запросами из указанной папки."""
    url = url + slug + '/browse' + f'?limit={limit}'
    response = requests.get(
        url,
        auth=(
            cn.get_bitbucket_username(),
            cn.get_bitbucket_password()
        ),
        verify=False
    )

    sql_files = []
    pattern = r'.+\.sql\b'
    for f_data in response.json()['children']['values']:
        title = f_data['path']['name']
        if fullmatch(pattern, title):
            sql_files.append({
                "name": title,
                "description": title[:-4]
            })

    return sql_files


@custom_logging_decorator(logger)
def get_remote_sql(query_dir: str, sql_title: str) -> str:
    """
    Получить текст sql-запроса из удалённого репозитория на BitBucket.

    :param query_dir: папка с файлами на BitBucket
    :param sql_title: название файла с расширением .sql
    :return: текст запроса
    """
    sql_query_url = OSSKTB_PROJECT_URL + query_dir + '/browse/' + sql_title + '?at=master'
    try:
        response = requests.get(
            sql_query_url,
            auth=(
                cn.get_bitbucket_username(),
                cn.get_bitbucket_password()
            ),
            verify=False
        ).json()
        return '\n'.join((d['text'] for d in response['lines']))
    except Exception:
        raise BitBucketWorkError("НЕ был получен sql-запрос из BitBucket")
