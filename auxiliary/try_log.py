import logging
import requests

logging.basicConfig(level='DEBUG')
logger = logging.getLogger()


logging.getLogger('urllib3').setLevel('CRITICAL')


def main():
    logger.debug(f'Start main()..')

    r = requests.get('https://www.google.ru')


if __name__ == '__main__':
    main()
