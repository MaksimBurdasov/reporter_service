from spring_config import ClientConfigurationBuilder
from spring_config.client import SpringConfigClient

configuration = (
    ClientConfigurationBuilder()
    .app_name("ossktb-rcsite-reporter")  # config file
    .address("http://ossktbapprhel1/ossktb-rcsite-settings/")
    .profile("prod")
    .build()
)

# cnf - настройки (конфигурация) проекта, которые возвращает сервис settings
cnf = SpringConfigClient(configuration).get_config()


def get_dj_secret() -> str:
    """Получить секретный ключ SECRET_KEY."""
    return cnf['django_secret_key']


def get_db_user() -> str:
    """Получить логин тех. пользователя для доступа к БД."""
    return cnf['db']['db_user']


def get_db_pass() -> str:
    """Получить пароль тех. пользователя для доступа к БД."""
    return cnf['db']['db_pass']


def get_bitbucket_username() -> str:
    """Получить логин тех. пользователя для доступа к BitBucket."""
    return cnf['bitbucket']['un']


def get_bitbucket_password() -> str:
    """Получить пароль тех. пользователя для доступа к BitBucket."""
    return cnf['bitbucket']['pw']


def get_mail_host() -> str:
    """Получить хост сервера, с которого будут отправляться письма."""
    return cnf['mail']['host']


def get_tech_un() -> str:
    return cnf['tech_domain_user']['un']


def get_tech_pw() -> str:
    return cnf['tech_domain_user']['pw']
