"""Index page."""
import collections
import datetime
import flask
import os
import requests

from dnstwister import app

PAPERTRAIL_API = 'https://papertrailapp.com/api/v1/events/search.json'
FILTER = 'status=5 OR exception OR error:'


def extract_to_hour(event_time_str):
    """Convert timestamp to datetime at nearest (floor) hour."""
    when = datetime.datetime.strptime(
        event_time_str.split('+')[0], '%Y-%m-%dT%H:%M:%S'
    )
    return when.replace(minute=0, second=0, microsecond=0)


def get_dataclip():
    """Return dataclip status info."""
    try:
        return requests.get(os.environ['MONITORING_DATACLIP']).json()
    except Exception as ex:
        app.logger.error(
            'Unable to retrieve monitoring dataclip: {}'.format(ex)
        )
        flask.abort(500)


def get_logged():
    """Return log stats."""
    try:
        json = requests.get(
            PAPERTRAIL_API,
            {'q': FILTER},
            headers={'X-Papertrail-Token': os.environ['PAPERTRAIL_TOKEN']},
        ).json()
    except Exception as ex:
        app.logger.error(
            'Unable to retrieve papertrail data: {}'.format(ex)
        )
        flask.abort(500)

    hourly_events = [extract_to_hour(event['generated_at'])
                     for event
                     in json['events']]

    totals_per_hour = collections.defaultdict(int)
    for when in hourly_events:
        totals_per_hour[when] += 1

    return totals_per_hour


@app.route(r'/status')
def status():
    """Status page."""
    dataclip_status = get_dataclip()
    log_stats = get_logged()
    print log_stats
    return flask.render_template(
        'www/status.html',
        summary=all(dataclip_status['values'][0]),
        statuses=zip(dataclip_status['fields'], dataclip_status['values'][0]),
    )
