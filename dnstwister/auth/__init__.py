"""Google Authentication View Decorators."""
from functools import wraps
from flask import request, redirect, url_for, session
from urllib2 import Request, urlopen, URLError

import os
import json

from time import time
from base64 import b64decode


GOOGLE_AUTH = os.getenv('GOOGLE_AUTH')
CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
EMAIL_DOMAIN = os.getenv('GOOGLE_EMAIL_DOMAIN')


def login_required(view):
    @wraps(view)
    def is_authenticated(*args, **kwargs):
        if GOOGLE_AUTH == 'false':
            return view (*args, **kwargs)
        try:
            access_token = session.get('access_token')[0]
            id_token = session.get('id_token')[0]
        except:
            return redirect(url_for('login'))
        if True in {access_token is None, id_token is None}:
            return redirect(url_for('login'))
        try:
            token_body = id_token.split('.')[1]
            parsed_token = json.loads(b64decode(token_body + '==='))
            token_issuer = parsed_token['iss'] == 'accounts.google.com'
            token_audience = parsed_token['aud'] == CLIENT_ID
            token_domain = parsed_token['hd'] == EMAIL_DOMAIN
            token_expires = int(parsed_token['exp']) >= int(time())
        except:
            session.pop('access_token', None)
            session.pop('id_token', None)
            return 'Unauthorized exception'
        if False in {token_issuer, token_audience, token_domain}:
            return 'Unauthorized!<br>issuer: ' + str(token_issuer) + '<br>audience: ' + str(token_audience) + '<br>domain: ' + str(token_domain)
        if token_expires is False:
            return redirect(url_for('login'))
        if access_token is None:
            return redirect(url_for('login'))
        headers = { 'Authorization': 'OAuth ' + access_token }
        req = Request('https://www.googleapis.com/oauth2/v1/userinfo', None, headers)
        try:
            res = urlopen(req)
        except URLError, e:
            if e.code == 401:
                session.pop('id_token', None)
                session.pop('access_token', None)
            return redirect(url_for('login', next=request.url))
        return view(*args, **kwargs)
    return is_authenticated
