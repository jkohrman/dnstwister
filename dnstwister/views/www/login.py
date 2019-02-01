"""Authentication pages"""
import flask
import os
import requests

from flask import request, session, redirect, url_for

from dnstwister import app
import dnstwister.auth as auth


@app.route(r'/login')
def login():
    CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
    SCOPE = os.getenv('GOOGLE_SCOPE')
    oauthurl = 'https://accounts.google.com/o/oauth2/auth?client_id=' + CLIENT_ID + '&redirect_uri=' + REDIRECT_URI + '&scope=' + SCOPE + '&response_type=code'
    next = request.args.get('next')
    if next:
        session['next'] = next
        oauthurl = oauthurl + '&next=' + next
    return redirect(oauthurl)

@app.route(r'/login/callback')
@google.authorized_handler
def authorized():
    data = 'code=' + request.args.get('code') + '&client_id=' + CLIENT_ID + '&client_secret=' + CLIENT_SECRET + '&redirect_uri=' + REDIRECT_URI + '&grant_type=authorization_code'
    res = requests.post(url='https://accounts.google.com/o/oauth2/token', data=data)
    access_token = res['access_token']
    session['access_token'] = access_token, ''
    next = session['next']
    session['next'] = ''
    try:
        dest = url_for(next)
    except:
        return redirect(url_for('index'))
    return redirect(dest)

@app.route(r'/logout')
def logout():
    del session['access_token']
    session.modified = True
    return redirect('/')
