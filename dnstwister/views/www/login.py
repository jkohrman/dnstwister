"""Authentication pages"""
import flask
import os
import json

from time import time
from base64 import urlsafe_b64encode, b64decode

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import request, session, redirect, url_for

from dnstwister import app
import dnstwister.auth as auth


GOOGLE_AUTH = os.getenv('GOOGLE_AUTH')
CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
EMAIL_DOMAIN = os.getenv('GOOGLE_EMAIL_DOMAIN')
SCOPE = os.getenv('GOOGLE_SCOPE')


@app.route(r'/login')
def login():
    if GOOGLE_AUTH is 'false':
        return redirect(url_for('index'))
    state = urlsafe_b64encode(os.urandom(24))
    session['google_state'] = state
    oauthurl = 'https://accounts.google.com/o/oauth2/auth?client_id=' + CLIENT_ID + '&redirect_uri=' + REDIRECT_URI + '&scope=' + SCOPE + '&response_type=code&state=' + state
    if EMAIL_DOMAIN is not None:
        oauthurl = oauthurl + '&hd=' + EMAIL_DOMAIN
    next_dest = request.args.get('next')
    if next_dest is not None:
        session['next'] = next_dest
        oauthurl = oauthurl + '&next=' + next_dest
    return redirect(oauthurl)

@app.route(r'/login/callback')
def authorized():
    if GOOGLE_AUTH is 'false':
        return redirect(url_for('index'))
    if request.args.get('error') is not None:
        session.pop('next', None)
        session.pop('access_token', None)
        return request.args.get('error')
        return redirect(url_for('index'))
    google_state = request.args.get('state')
    session_state = session['google_state']
    if google_state != session_state:
        session.pop('google_state', None)
        session.pop('next', None)
        session.pop('access_token', None)
        return 'CSRF Error: Token mismatch!<br>' + session_state + '<br>' + google_state
    next_dest = request.args.get('next')
    auth_code = request.args.get('code')
    data = {
        'code': auth_code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    url = 'https://accounts.google.com/o/oauth2/token'
    req = Request(url, urlencode(data).encode())
    res = json.loads(urlopen(req).read().decode())
    access_token = res['access_token']
    id_token = res['id_token']
    try:
        token_body = id_token.split('.')[1]
        parsed_token = json.loads(b64decode(token_body + '==='))
        token_issuer = parsed_token['iss'] == 'accounts.google.com'
        token_audience = parsed_token['aud'] == CLIENT_ID
        token_domain = parsed_token['hd'] == EMAIL_DOMAIN
        token_issued = int(time()) - 10 <= int(parsed_token['iat']) <= int(time()) + 10
        token_expires = int(parsed_token['exp']) >= int(time())
    except:
        session.pop('google_state', None)
        session.pop('next', None)
        session.pop('access_token', None)
        session.pop('id_token', None)
        return 'Unauthorized exception: '
    if False in {token_issuer, token_audience, token_domain, token_issued, token_expires}:
        return 'Unauthorized:<br>issuer: ' + str(token_issuer) + '<br>audience: ' + str(token_audience) + '<br>domain: ' + str(token_domain) + '<br>issued: ' + str(token_issued) + '<br>expires: ' + str(token_expires)
    session['id_token'] = id_token, ''
    session['access_token'] = access_token, ''
    if 'next' in session:
        next_dest = session['next']
        session.pop('next', None)
        try:
            dest = url_for(next_dest)
        except:
            dest = redirect(url_for('index'))
    else:
        dest = url_for('index')
    return redirect(dest)

@app.route(r'/logout')
def logout():
    session.pop('access_token', None)
    session.pop('id_token', None)
    del session['access_token']
    del session['id_token']
    session.modified = True
    return redirect('/')
