import requests

import logging
from report_app.report_logic.custom_decorators import custom_logging_decorator


logger = logging.getLogger(__name__)


@custom_logging_decorator(logger)
def validate(token):
    url = 'http://ossktbapprhel1/ossktb-rcsite-ad-api/api/auth/validate'
    headers = {'Authorization': token}
    response = requests.get(url, headers=headers).json()
    if 'payload' in response and 'username' in response['payload']:
        logger.debug("пользователь найден")
        return response['payload']['username']
    else:
        logger.debug("пользователь не определен")
        return None


@custom_logging_decorator(logger)
def get_info(user):
    url = 'http://ossktbapprhel1/ossktb-rcsite-ad-api/api/employees/' + user
    response = requests.get(url).json()
    if 'groups' in response and 'Support_RC' or 'DSBP' in response['groups']:
        return response
    else:
        return None