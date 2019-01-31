"""Domain analysis page."""
import flask

from dnstwister import app
import dnstwister.tools as tools
import dnstwister.auth as auth


@app.route('/analyse/<hexdomain>')
@auth.login_required
def analyse(hexdomain):
    """Do a domain analysis."""
    domain = tools.parse_domain(hexdomain)
    if domain is None:
        flask.abort(
            400,
            'Malformed domain or domain not represented in hexadecimal format.'
        )

    return flask.render_template(
        'www/analyse.html',
        domain=domain,
        hexdomain=hexdomain,
    )
