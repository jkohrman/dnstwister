"""Authentication pages"""
import flask
import os
import json

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import request, session, redirect, url_for

from dnstwister import app
import dnstwister.auth as auth


CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
SCOPE = os.getenv('GOOGLE_SCOPE')


@app.route(r'/login')
def login():
    oauthurl = 'https://accounts.google.com/o/oauth2/auth?client_id=' + CLIENT_ID + '&redirect_uri=' + REDIRECT_URI + '&scope=' + SCOPE + '&response_type=code'
    next_dest = request.args.get('next')
    if next_dest:
        session['next'] = next_dest
        oauthurl = oauthurl + '&next=' + next_dest
    return redirect(oauthurl)

@app.route(r'/login/callback')
def authorized():
    next_dest = request.args.get('next'), False
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
    del session['access_token']
    session.modified = True
    return redirect('/')
