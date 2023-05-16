"""
Custom authentication class for DRF and JWT
https://github.com/encode/django-rest-framework/blob/master/rest_framework/authentication.py
"""

from django.contrib.auth import get_user_model

from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

from report_app.report_logic.rc_site_auth import *


class ExternalJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        user = get_user_model()

        access_token = request.headers.get('ad-token')
        if access_token is None:
            return None

        un = validate(access_token)
        if un is None:
            raise exceptions.AuthenticationFailed('User not found')
        user.USERNAME_FIELD = un

        user_info = get_info(un)
        if user_info is None:
            raise exceptions.AuthenticationFailed('No user information')
        user.EMAIL_FIELD = user_info["mail"]

        return user, None
