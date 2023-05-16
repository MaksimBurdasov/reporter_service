from report_app.customauth import ExternalJWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import APIView

from traceback import format_exc

from report_app.report_logic.bitbucket_liaison import *
from report_app.report_logic.main import magic_away_from_Hogwarts

from report_app.report_logic.database_manipulator import get_servers_info

logger = logging.getLogger(__name__)


class HealthAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Проверить работоспособность сервиса."""
        status_code = status.HTTP_200_OK
        content = {
            "status": 'I am totally fine!'
        }
        logger.debug("Вызван метод /health")
        return Response(content, status=status_code)


class FoldersAPIView(APIView):
    authentication_classes = [ExternalJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Вернуть список названий папок с sql-скриптами."""
        status_code = status.HTTP_200_OK
        content = {
            "folders": []
        }
        try:
            content["folders"] = get_folders_list()
        except Exception as error:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            content["errorMessage"] = f"{type(error).__name__}: {error}"
            content["errorTrace"] = format_exc()
            logger.exception(request.user.USERNAME_FIELD + " Не удалось получить список папок BitBucket.")

        logger.warning("выполнен метод getFolders")
        return Response(content, status=status_code)


class QueriesAPIView(APIView):
    authentication_classes = [ExternalJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Вернуть список sql-скриптов из указанной дирректории на BitBucket."""
        status_code = status.HTTP_200_OK
        content = {
            "queries": []
        }

        if 'folder' in request.query_params:
            fld = request.query_params['folder']
            try:
                content["queries"] = get_files_list(fld)
            except Exception as error:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                content["errorMessage"] = f"{type(error).__name__}: {error}"
                content["errorTrace"] = format_exc()
                logger.exception(request.user.USERNAME_FIELD + " Не удалось получить список sql-скриптов BitBucket.")
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            content["errorMessage"] = "Ошибка. В GET-запросе отсутствует параметр 'folder'"
            content["errorTrace"] = "Ошибка пользователя, технической проблемы нет."

        logger.warning("выполнен метод getQueries")
        return Response(content, status=status_code)


class DBInfoAPIView(APIView):
    authentication_classes = [ExternalJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Вернуть список серверов с базами данных."""
        status_code = status.HTTP_200_OK
        content = {
            "servers": []
        }

        try:
            content["servers"] = get_servers_info()
        except Exception as error:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            content["errorMessage"] = f"{type(error).__name__}: {error}"
            content["errorTrace"] = format_exc()
            logger.exception(request.user.USERNAME_FIELD + " Не удалось получить список серверов с базами данных.")

        logger.warning("выполнен метод getDBServers")
        return Response(content, status=status_code)


class OneQueryAPIView(APIView):
    authentication_classes = [ExternalJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Вернуть текст одного .sql файла."""
        status_code = status.HTTP_200_OK
        content = {
            "sql": "-- Ошибка получения.\n-- Важно: параметры 'directory', 'sql_title' необходимо указывать в URL."}

        try:
            content["sql"] = get_remote_sql(
                request.query_params["directory"],
                request.query_params["sql_title"]
            )
        except Exception as error:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            content["errorMessage"] = f"{type(error).__name__}: {error}"
            content["errorTrace"] = format_exc()
            logger.exception(request.user.USERNAME_FIELD + " Не удалось получить текст скрипта из BitBucket.")

        logger.warning("выполнен метод getSQL")
        return Response(content, status=status_code)


class SendAPIView(APIView):
    """Представление обработки метода sendReport."""

    authentication_classes = [ExternalJWTAuthentication]
    permission_classes = [IsAuthenticated]

    required = {
        "sql_title": "[обязательный] Название файла (с расширением .sql)",
        "sql_query": "[обязательный] Текст sql-запроса, полученный из формы для редактирования",
        "db_server": "[обязательный] Сервер, на котором выполнится sql-запрос",
        "file_format": "[обязательный] Формат файла с отчётом (доступны xlsx и csv)",
        "recipients": "[обязательный] Список почтовых адресов получателей отчёта",
    }

    optional = {
        "database": "[доп] БД, в которой выполнится sql-запрос ('master' по умолчанию)",
        "carbon_copy": "[доп] Список почтовых адресов в копию (['support_rc_ndo@alfabank.ru'] по умолчанию)",
    }

    def get(self, request):
        """Вернуть информацию о параметрах метода sendReport."""
        return Response(
            {"info": "Выполнен GET-запрос метода sendReport. Ниже перечислены параметры POST-запроса"} |
            self.required | self.optional
        )

    def post(self, request):
        """Запустить функцию формирования и раcсылки отчёта."""
        status_code = status.HTTP_200_OK
        content = {}

        post_params = set(request.data)  # множество параметров POST-запроса

        # Проверка наличия необходимых параметров в теле запроса
        logger.warning("началась проверка параметров для формирования отчёта")
        if set(self.required).issubset(post_params):
            logger.warning("все необходимые параметры указаны")
            try:
                magic_away_from_Hogwarts(
                    request.data.pop("sql_title"), request.data.pop("sql_query"),
                    request.data.pop("db_server"), request.data.pop("file_format"),
                    request.data.pop("recipients"), carbon_copy=[request.user.EMAIL_FIELD],
                    **request.data
                )
            except Exception as error:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                content["errorMessage"] = f"{type(error).__name__}: {error}"
                content["errorTrace"] = format_exc()
                logger.exception(request.user.USERNAME_FIELD + " Ошибка формирования отчёта.")
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            content["errorMessage"] = 'В теле POST-запроса отсутствуют необходимые параметры: ' + \
                                      '; '.join(set(self.required).difference(post_params))
            content["errorTrace"] = "Ошибка пользователя, технической проблемы нет."
        return Response(content, status=status_code)
