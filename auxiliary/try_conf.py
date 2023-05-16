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
    """Получить секретный ключ Django админа."""
    print(cnf)
    return cnf['django_secret_key']

print(get_dj_secret())
