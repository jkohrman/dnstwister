"""Google Authentication View Decorators."""
from functools import wraps
from flask import request, redirect, url_for, session

def login_required(view):
    @wraps(view)
    def is_authenticated(*args, **kwargs):
        access_token = session.get('access_token')
        if access_token is None:
            return redirect(url_for('login'))

        access_token = access_token[0]
        from urllib2 import Request, urlopen, URLError
        
        headers = { 'Authorization': 'OAuth ' + access_token }
        req = Request('https://www.googleapis.com/oauth2/v1/userinfo', None, headers)
        try:
            res = urlopen(req)
        except URLError, e:
            if e.code == 401:
                session.pop('access_token', None)
            return redirect(url_for('login', next=request.url))
        return view(*args, **kwargs)
    return is_authenticated
