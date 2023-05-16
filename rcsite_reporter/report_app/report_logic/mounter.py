import os
import subprocess

import logging
from report_app.report_logic.custom_decorators import custom_logging_decorator

import report_app.report_logic.config as cn

from report_app.report_logic.custom_errors import MountFolderError


logger = logging.getLogger(__name__)

network_folder = "//bpdb1/shar_all/ReporterDepot"  # сетевая папка
container_folder = "/mnt/ReporterDepot"  # папка внутри контейнера


@custom_logging_decorator(logger)
def mount_depot_dir(web_dir: str = network_folder, bin_dir: str = container_folder) -> None:
    """
    Примонтировать папку, выполнив команду mount в Docker-контейнере
    Подробнее про unix-команду MOUNT: https://internet-lab.ru/linux_mount_cifs

    :param web_dir: сетевая папка (шара) для выгрузки отчётов
    :param bin_dir: примонтированная папка внутри контейнера (bin - англ. контейнер)
    :return: None
    """

    mount_options = ','.join((
        f"username={cn.get_tech_un()}",
        f"password='{cn.get_tech_pw()}'",
        "domain=moscow.alfaintra.net",
        "vers=2.0",
        "iocharset=utf8",
        "cache=loose",
        "noperm"
    ))
    cmd = f"mount -t cifs -v {web_dir} {bin_dir} -o {mount_options}"
    subprocess.run(cmd, shell=True, capture_output=True, text=True)


@custom_logging_decorator(logger)
def is_mounted(dir_name: str) -> bool:
    if dir_name in subprocess.run("findmnt", shell=True, capture_output=True, text=True).stdout:
        return True
    return False


@custom_logging_decorator(logger)
def is_mount_ready(bin_dir: str = container_folder) -> bool:
    """Проверить готовность монтированной папки."""
    if not os.path.exists(bin_dir):
        raise MountFolderError(f"НЕ найдена папка {bin_dir} для монтирования")

    if is_mounted(bin_dir):
        logger.warning(f"сетевая папка найдена: {bin_dir}")
        return True

    logger.warning(f"требуется примонтировать папку {bin_dir}")
    for _ in range(3):
        mount_depot_dir(web_dir=network_folder, bin_dir=bin_dir)
        if is_mounted(bin_dir):
            logger.warning("папка успешно примонтирована")
            return True

    logger.warning(f"не удалось примонтировать папку {bin_dir}")
    return False
