import subprocess


def mount_depot_dir(web_dir: str = "//bpdb1/shar_all/ReporterDepot", bin_dir: str = "mnt/ReporterDepot") -> None:
    """
    Примонтировать папку, выполнив команду mount в Docker-контейнере

    :param web_dir: сетевая папка (шара) для выгрузки отчётов
    :param bin_dir: примонтированная папка внутри контейнера
    :return: None
    """

    win_un = "OSSKTBAdmin"  # TODO: заменить
    win_pw = "OSSKTBPass1234"  # TODO: заменить

    mount_options = ','.join((
        f"username={win_un}",
        f"password='{win_pw}'",
        "domain=moscow.alfaintra.net",
        "vers=2.0",
        "iocharset=utf8",
        "cache=loose",
        "noperm"
    ))

    cmd = f"mount -t cifs -v -o {mount_options} {web_dir} {bin_dir}"
    subprocess.run(cmd, shell=True, capture_output=True, text=True)


def is_dir_exist(dir_name: str) -> None:
    if dir_name in subprocess.run('df -h ' + dir_name, shell=True, capture_output=True, text=True).stderr:
        return True
    return False


def is_mount_ready(bin_dir: str = "/mnt/ReporterDepot") -> None:
    """Проверить готовность монтированной папки"""
    if is_dir_exist(bin_dir):
        return True
    for _ in range(3):
        mount_depot_dir()
        if is_dir_exist(bin_dir):
            return True
    return False


