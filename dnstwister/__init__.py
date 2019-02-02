#pylint: skip-file
"""dnstwister web app.

This is the pattern from http://flask.pocoo.org/docs/0.11/patterns/packages/
which generates circular imports hence the comment at the top to just ignore
this file.
"""
import flask
import flask_cache
import logging
import os

from flask import session

import mail.sendgridservice
import storage.pg_database
import storage.redis_stats_store


# Set up app/cache/db/emailer/gateway here
app = flask.Flask(__name__)
cache = flask_cache.Cache(app, config={'CACHE_TYPE': 'simple'})
data_db = storage.pg_database.PGDatabase()
emailer = mail.sendgridservice.SGSender()
stats_store = storage.redis_stats_store.RedisStatsStore()

# Logging
app.logger.setLevel(logging.INFO)

# Session
app.secret_key = os.getenv('SESSION_SECRET')

# Blueprints
import api
app.register_blueprint(api.app, url_prefix='/api')

# Import modules using dnstwister.app/cache/db/emailer here.
import repository
import tools
import tools.template
import views.syndication.atom
import views.www.analyse
import views.www.email
import views.www.help
import views.www.index
import views.www.search
import views.www.status
import views.www.login

# Filters
app.jinja_env.filters['domain_renderer'] = tools.template.domain_renderer
app.jinja_env.filters['domain_encoder'] = tools.template.domain_encoder
