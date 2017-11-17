"""Tests of the atom behaviour."""
# -*- coding: UTF-8 -*-
import base64
import datetime
import textwrap
import unittest

import pytest
import flask.ext.webtest
import mock
import webtest.app

import dnstwister
from dnstwister import tools
import patches


@mock.patch('dnstwister.repository.db', patches.SimpleKVDatabase())
def test_unicode_atom(webapp):
    """Unicode should just work too, this is just a sanity check."""
    unicode_domain =  'xn--plnt-1na.com'.decode('idna')  # 'plànt.com'
    get_path = tools.encode_domain(unicode_domain)
    webapp.get('/atom/{}'.format(get_path))


def test_atom_feeds_validate_domain(webapp):
    """Test that the validation checks for valid domains before creating
    feeds.
    """
    with pytest.raises(webtest.app.AppError) as err:
        webapp.get('/atom/324u82938798swefsdf')
    assert '400 BAD REQUEST' in err.value.message


# TODO: Update to pytest-style.
class TestAtom(unittest.TestCase):
    """Tests of the atom feed behaviour."""

    def setUp(self):
        """Set up the app for testing."""
        # Create a webtest Test App for use
        self.app = flask.ext.webtest.TestApp(dnstwister.app)

        # Clear the webapp cache
        dnstwister.cache.clear()

    @mock.patch('dnstwister.repository.db', patches.SimpleKVDatabase())
    def test_new_feed(self):
        """Tests the registration of a new feed."""
        repository = dnstwister.repository

        # We need a domain to get the feed for.
        domain = 'www.example.com'

        # A feed is registered by trying to load it (and it not already being
        # registered).
        res = self.app.get('/atom/{}'.format(base64.b64encode(domain))).follow()

        # And only returns a single placeholder item.
        assert str(res) == textwrap.dedent("""
            Response: 200 OK
            Content-Type: application/atom+xml; charset=utf-8
            <?xml version="1.0" encoding="utf-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title type="text">dnstwister report for www.example.com</title>
              <id>http://localhost:80/atom/7777772e6578616d706c652e636f6d</id>
              <updated>{date_today}</updated>
              <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
              <link href="http://localhost:80/atom/7777772e6578616d706c652e636f6d" rel="self" />
              <generator>Werkzeug</generator>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">No report yet for www.example.com</title>
                <id>waiting:www.example.com</id>
                <updated>{date_today}</updated>
                <published>{date_today}</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
                <content type="html">&lt;p&gt;
                This is the placeholder for your dnstwister report for www.example.com.
            &lt;/p&gt;
            &lt;p&gt;
                Your first report will be generated within 24 hours with all entries
                marked as &quot;NEW&quot;.
            &lt;/p&gt;
            &lt;p&gt;
                &lt;strong&gt;Important:&lt;/strong&gt; The &quot;delta&quot; between each report is generated
                every 24 hours. If your feed reader polls this feed less often than that,
                you will miss out on changes.
            &lt;/p&gt;</content>
              </entry>
            </feed>
        """).strip().format(
            date_today=datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ).strftime('%Y-%m-%dT%H:%M:%SZ')
        )

        # Clear the webapp cache
        dnstwister.cache.clear()

        # Until the first delta is actually created, this placeholder remains.
        res = self.app.get('/atom/{}'.format(base64.b64encode(domain))).follow()
        assert str(res) == textwrap.dedent("""
            Response: 200 OK
            Content-Type: application/atom+xml; charset=utf-8
            <?xml version="1.0" encoding="utf-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title type="text">dnstwister report for www.example.com</title>
              <id>http://localhost:80/atom/7777772e6578616d706c652e636f6d</id>
              <updated>{date_today}</updated>
              <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
              <link href="http://localhost:80/atom/7777772e6578616d706c652e636f6d" rel="self" />
              <generator>Werkzeug</generator>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">No report yet for www.example.com</title>
                <id>waiting:www.example.com</id>
                <updated>{date_today}</updated>
                <published>{date_today}</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
                <content type="html">&lt;p&gt;
                This is the placeholder for your dnstwister report for www.example.com.
            &lt;/p&gt;
            &lt;p&gt;
                Your first report will be generated within 24 hours with all entries
                marked as &quot;NEW&quot;.
            &lt;/p&gt;
            &lt;p&gt;
                &lt;strong&gt;Important:&lt;/strong&gt; The &quot;delta&quot; between each report is generated
                every 24 hours. If your feed reader polls this feed less often than that,
                you will miss out on changes.
            &lt;/p&gt;</content>
              </entry>
            </feed>
        """).strip().format(
            date_today=datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ).strftime('%Y-%m-%dT%H:%M:%SZ')
        )

        # We can calculate a delta though.
        update_date = datetime.datetime(2016, 2, 28, 11, 10, 34)
        repository.update_delta_report(
            domain, {
                'new': [('www.examp1e.com', '127.0.0.1')],
                'updated': [],
                'deleted': [],
            },
            update_date
        )

        # Clear the webapp cache
        dnstwister.cache.clear()

        res = self.app.get('/atom/{}'.format(base64.b64encode(domain))).follow()
        assert str(res) == textwrap.dedent("""
            Response: 200 OK
            Content-Type: application/atom+xml; charset=utf-8
            <?xml version="1.0" encoding="utf-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title type="text">dnstwister report for www.example.com</title>
              <id>http://localhost:80/atom/7777772e6578616d706c652e636f6d</id>
              <updated>2016-02-28T11:10:34Z</updated>
              <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
              <link href="http://localhost:80/atom/7777772e6578616d706c652e636f6d" rel="self" />
              <generator>Werkzeug</generator>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">NEW: www.examp1e.com</title>
                <id>new:www.examp1e.com:127.0.0.1:1456657834.0</id>
                <updated>2016-02-28T11:10:34Z</updated>
                <published>2016-02-28T11:10:34Z</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
                <content type="html">&lt;h1&gt;IP: 127.0.0.1&lt;/h1&gt;
            &lt;a href=&quot;https://dnstwister.report/analyse/7777772e6578616d7031652e636f6d&quot;&gt;analyse&lt;/a&gt;</content>
              </entry>
            </feed>
        """).strip()

    @mock.patch('dnstwister.repository.db', patches.SimpleKVDatabase())
    def test_deleted_items_appear_in_rss(self):
        """Tests that deleted items in delta reports appear in the RSS.
        """
        repository = dnstwister.repository

        # We need a domain to get the feed for.
        domain = 'www.example.com'

        # We can calculate a delta though.
        update_date = datetime.datetime(2016, 2, 28, 11, 10, 34)
        repository.update_delta_report(
            domain, {
                'new': [('www.examp1e.com', '127.0.0.1')],
                'updated': [('wwwexa.mple.com', '127.0.0.1', '127.0.0.2')],
                'deleted': ['www.eeexample.com', 'www2.example.com.au'],
            },
            update_date
        )

        # Clear the webapp cache
        dnstwister.cache.clear()

        res = self.app.get('/atom/{}'.format(base64.b64encode(domain))).follow()
        assert str(res) == textwrap.dedent("""
            Response: 200 OK
            Content-Type: application/atom+xml; charset=utf-8
            <?xml version="1.0" encoding="utf-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title type="text">dnstwister report for www.example.com</title>
              <id>http://localhost:80/atom/7777772e6578616d706c652e636f6d</id>
              <updated>2016-02-28T11:10:34Z</updated>
              <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
              <link href="http://localhost:80/atom/7777772e6578616d706c652e636f6d" rel="self" />
              <generator>Werkzeug</generator>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">NEW: www.examp1e.com</title>
                <id>new:www.examp1e.com:127.0.0.1:1456657834.0</id>
                <updated>2016-02-28T11:10:34Z</updated>
                <published>2016-02-28T11:10:34Z</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
                <content type="html">&lt;h1&gt;IP: 127.0.0.1&lt;/h1&gt;
            &lt;a href=&quot;https://dnstwister.report/analyse/7777772e6578616d7031652e636f6d&quot;&gt;analyse&lt;/a&gt;</content>
              </entry>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">UPDATED: wwwexa.mple.com</title>
                <id>updated:wwwexa.mple.com:127.0.0.1:127.0.0.2:1456657834.0</id>
                <updated>2016-02-28T11:10:34Z</updated>
                <published>2016-02-28T11:10:34Z</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
                <content type="html">&lt;h1&gt;IP: 127.0.0.1 &amp;gt; 127.0.0.2&lt;/h1&gt;
            &lt;a href=&quot;https://dnstwister.report/analyse/7777776578612e6d706c652e636f6d&quot;&gt;analyse&lt;/a&gt;</content>
              </entry>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">DELETED: www.eeexample.com</title>
                <id>deleted:www.eeexample.com:1456657834.0</id>
                <updated>2016-02-28T11:10:34Z</updated>
                <published>2016-02-28T11:10:34Z</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
              </entry>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">DELETED: www2.example.com.au</title>
                <id>deleted:www2.example.com.au:1456657834.0</id>
                <updated>2016-02-28T11:10:34Z</updated>
                <published>2016-02-28T11:10:34Z</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
              </entry>
            </feed>
        """).strip()

    @mock.patch('dnstwister.repository.db', patches.SimpleKVDatabase())
    def test_feed_reading_is_tracked(self):
        """Tests that reading a feed is logged."""
        repository = dnstwister.repository

        domain = 'www.example.com'
        b64domain = base64.b64encode(domain)

        # Read dates are None by default
        read_date = repository.delta_report_last_read(domain)
        assert read_date is None

        # Registering a feed will update the read date
        self.app.get('/atom/{}'.format(b64domain)).follow()
        read_date = repository.delta_report_last_read(domain)
        assert type(read_date) is datetime.datetime

        # Manually set the date to an older date so we don't have to 'sleep'
        # in the test.
        repository.mark_delta_report_as_read(
            domain, datetime.datetime(2000, 1, 1, 0, 0, 0)
        )

        # Clear the webapp cache
        dnstwister.cache.clear()

        # Reading a feed will update the read date
        read_date = repository.delta_report_last_read(domain)
        self.app.get('/atom/{}'.format(b64domain)).follow()
        read_date2 = repository.delta_report_last_read(domain)

        assert read_date2 > read_date

    @mock.patch('dnstwister.repository.db', patches.SimpleKVDatabase())
    def test_unregister_tidies_database(self):
        """Tests that you can unregister domains."""
        repository = dnstwister.repository

        domain = 'www.example.com'
        b64domain = base64.b64encode(domain)

        assert not repository.is_domain_registered(domain)
        assert repository.db.data == {}

        self.app.get('/atom/{}'.format(b64domain)).follow()
        repository.update_delta_report(
            domain, {
                'new': [('www.examp1e.com', '127.0.0.1')],
                'updated': [],
                'deleted': [],
            },
        )

        assert repository.is_domain_registered(domain)
        assert repository.db.data != {}

        repository.unregister_domain(domain)

        assert not repository.is_domain_registered(domain)
        assert repository.db.data == {}


# TODO: Update to pytest-style.
class TestAtomUnicode(unittest.TestCase):
    """Tests of the atom feed behaviour, with a Unicode domain."""

    def setUp(self):
        """Set up the app for testing."""
        # Create a webtest Test App for use
        self.app = flask.ext.webtest.TestApp(dnstwister.app)

        # Clear the webapp cache
        dnstwister.cache.clear()

    @mock.patch('dnstwister.repository.db', patches.SimpleKVDatabase())
    def test_new_feed(self):
        """Tests the registration of a new feed."""
        repository = dnstwister.repository

        # We need a domain to get the feed for.
        domain = u'www.\u0454xample.com'

        # A feed is registered by trying to load it (and it not already being
        # registered).
        res = self.app.get('/atom/{}'.format(tools.encode_domain(domain)))

        # And only returns a single placeholder item.
        assert str(res) == textwrap.dedent("""
            Response: 200 OK
            Content-Type: application/atom+xml; charset=utf-8
            <?xml version="1.0" encoding="utf-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title type="text">dnstwister report for www.\xd1\x94xample.com (www.xn--xample-9uf.com)</title>
              <id>http://localhost:80/atom/7777772e786e2d2d78616d706c652d3975662e636f6d</id>
              <updated>{date_today}</updated>
              <link href="http://localhost:80/search/7777772e786e2d2d78616d706c652d3975662e636f6d" />
              <link href="http://localhost:80/atom/7777772e786e2d2d78616d706c652d3975662e636f6d" rel="self" />
              <generator>Werkzeug</generator>
              <entry xml:base="http://localhost:80/atom/7777772e786e2d2d78616d706c652d3975662e636f6d">
                <title type="text">No report yet for www.\xd1\x94xample.com (www.xn--xample-9uf.com)</title>
                <id>waiting:www.\xd1\x94xample.com (www.xn--xample-9uf.com)</id>
                <updated>{date_today}</updated>
                <published>{date_today}</published>
                <link href="http://localhost:80/search/7777772e786e2d2d78616d706c652d3975662e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
                <content type="html">&lt;p&gt;
                This is the placeholder for your dnstwister report for www.\xd1\x94xample.com (www.xn--xample-9uf.com).
            &lt;/p&gt;
            &lt;p&gt;
                Your first report will be generated within 24 hours with all entries
                marked as &quot;NEW&quot;.
            &lt;/p&gt;
            &lt;p&gt;
                &lt;strong&gt;Important:&lt;/strong&gt; The &quot;delta&quot; between each report is generated
                every 24 hours. If your feed reader polls this feed less often than that,
                you will miss out on changes.
            &lt;/p&gt;</content>
              </entry>
            </feed>
        """).strip().format(
            date_today=datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ).strftime('%Y-%m-%dT%H:%M:%SZ')
        )

        # Clear the webapp cache
        dnstwister.cache.clear()

        # Until the first delta is actually created, this placeholder remains.
        res = self.app.get('/atom/{}'.format(tools.encode_domain(domain)))
        assert str(res) == textwrap.dedent("""
            Response: 200 OK
            Content-Type: application/atom+xml; charset=utf-8
            <?xml version="1.0" encoding="utf-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title type="text">dnstwister report for www.\xd1\x94xample.com (www.xn--xample-9uf.com)</title>
              <id>http://localhost:80/atom/7777772e786e2d2d78616d706c652d3975662e636f6d</id>
              <updated>{date_today}</updated>
              <link href="http://localhost:80/search/7777772e786e2d2d78616d706c652d3975662e636f6d" />
              <link href="http://localhost:80/atom/7777772e786e2d2d78616d706c652d3975662e636f6d" rel="self" />
              <generator>Werkzeug</generator>
              <entry xml:base="http://localhost:80/atom/7777772e786e2d2d78616d706c652d3975662e636f6d">
                <title type="text">No report yet for www.\xd1\x94xample.com (www.xn--xample-9uf.com)</title>
                <id>waiting:www.\xd1\x94xample.com (www.xn--xample-9uf.com)</id>
                <updated>{date_today}</updated>
                <published>{date_today}</published>
                <link href="http://localhost:80/search/7777772e786e2d2d78616d706c652d3975662e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
                <content type="html">&lt;p&gt;
                This is the placeholder for your dnstwister report for www.\xd1\x94xample.com (www.xn--xample-9uf.com).
            &lt;/p&gt;
            &lt;p&gt;
                Your first report will be generated within 24 hours with all entries
                marked as &quot;NEW&quot;.
            &lt;/p&gt;
            &lt;p&gt;
                &lt;strong&gt;Important:&lt;/strong&gt; The &quot;delta&quot; between each report is generated
                every 24 hours. If your feed reader polls this feed less often than that,
                you will miss out on changes.
            &lt;/p&gt;</content>
              </entry>
            </feed>
        """).strip().format(
            date_today=datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ).strftime('%Y-%m-%dT%H:%M:%SZ')
        )

        # We can calculate a delta though.
        update_date = datetime.datetime(2016, 2, 28, 11, 10, 34)
        repository.update_delta_report(
            domain, {
                'new': [(u'www.\u0454xampl\u0454.com', '127.0.0.1')],
                'updated': [],
                'deleted': [],
            },
            update_date
        )

        # Clear the webapp cache
        dnstwister.cache.clear()

        res = self.app.get('/atom/{}'.format(tools.encode_domain(domain)))
        assert str(res) == textwrap.dedent("""
            Response: 200 OK
            Content-Type: application/atom+xml; charset=utf-8
            <?xml version="1.0" encoding="utf-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title type="text">dnstwister report for www.\xd1\x94xample.com (www.xn--xample-9uf.com)</title>
              <id>http://localhost:80/atom/7777772e786e2d2d78616d706c652d3975662e636f6d</id>
              <updated>2016-02-28T11:10:34Z</updated>
              <link href="http://localhost:80/search/7777772e786e2d2d78616d706c652d3975662e636f6d" />
              <link href="http://localhost:80/atom/7777772e786e2d2d78616d706c652d3975662e636f6d" rel="self" />
              <generator>Werkzeug</generator>
              <entry xml:base="http://localhost:80/atom/7777772e786e2d2d78616d706c652d3975662e636f6d">
                <title type="text">NEW: www.\xd1\x94xampl\xd1\x94.com (www.xn--xampl-91ef.com)</title>
                <id>new:www.xn--xampl-91ef.com:127.0.0.1:1456657834.0</id>
                <updated>2016-02-28T11:10:34Z</updated>
                <published>2016-02-28T11:10:34Z</published>
                <link href="http://localhost:80/search/7777772e786e2d2d78616d706c652d3975662e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
                <content type="html">&lt;h1&gt;IP: 127.0.0.1&lt;/h1&gt;
            &lt;a href=&quot;https://dnstwister.report/analyse/7777772e786e2d2d78616d706c2d393165662e636f6d&quot;&gt;analyse&lt;/a&gt;</content>
              </entry>
            </feed>
        """).strip()

    @mock.patch('dnstwister.repository.db', patches.SimpleKVDatabase())
    def test_deleted_items_appear_in_rss(self):
        """Tests that deleted items in delta reports appear in the RSS.
        """
        repository = dnstwister.repository

        # We need a domain to get the feed for.
        domain = 'www.example.com'

        # We can calculate a delta though.
        update_date = datetime.datetime(2016, 2, 28, 11, 10, 34)
        repository.update_delta_report(
            domain, {
                'new': [('www.examp1e.com', '127.0.0.1')],
                'updated': [('wwwexa.mple.com', '127.0.0.1', '127.0.0.2')],
                'deleted': ['www.eeexample.com', 'www2.example.com.au'],
            },
            update_date
        )

        # Clear the webapp cache
        dnstwister.cache.clear()

        res = self.app.get('/atom/{}'.format(base64.b64encode(domain))).follow()
        assert str(res) == textwrap.dedent("""
            Response: 200 OK
            Content-Type: application/atom+xml; charset=utf-8
            <?xml version="1.0" encoding="utf-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title type="text">dnstwister report for www.example.com</title>
              <id>http://localhost:80/atom/7777772e6578616d706c652e636f6d</id>
              <updated>2016-02-28T11:10:34Z</updated>
              <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
              <link href="http://localhost:80/atom/7777772e6578616d706c652e636f6d" rel="self" />
              <generator>Werkzeug</generator>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">NEW: www.examp1e.com</title>
                <id>new:www.examp1e.com:127.0.0.1:1456657834.0</id>
                <updated>2016-02-28T11:10:34Z</updated>
                <published>2016-02-28T11:10:34Z</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
                <content type="html">&lt;h1&gt;IP: 127.0.0.1&lt;/h1&gt;
            &lt;a href=&quot;https://dnstwister.report/analyse/7777772e6578616d7031652e636f6d&quot;&gt;analyse&lt;/a&gt;</content>
              </entry>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">UPDATED: wwwexa.mple.com</title>
                <id>updated:wwwexa.mple.com:127.0.0.1:127.0.0.2:1456657834.0</id>
                <updated>2016-02-28T11:10:34Z</updated>
                <published>2016-02-28T11:10:34Z</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
                <content type="html">&lt;h1&gt;IP: 127.0.0.1 &amp;gt; 127.0.0.2&lt;/h1&gt;
            &lt;a href=&quot;https://dnstwister.report/analyse/7777776578612e6d706c652e636f6d&quot;&gt;analyse&lt;/a&gt;</content>
              </entry>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">DELETED: www.eeexample.com</title>
                <id>deleted:www.eeexample.com:1456657834.0</id>
                <updated>2016-02-28T11:10:34Z</updated>
                <published>2016-02-28T11:10:34Z</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
              </entry>
              <entry xml:base="http://localhost:80/atom/7777772e6578616d706c652e636f6d">
                <title type="text">DELETED: www2.example.com.au</title>
                <id>deleted:www2.example.com.au:1456657834.0</id>
                <updated>2016-02-28T11:10:34Z</updated>
                <published>2016-02-28T11:10:34Z</published>
                <link href="http://localhost:80/search/7777772e6578616d706c652e636f6d" />
                <author>
                  <name>dnstwister</name>
                </author>
              </entry>
            </feed>
        """).strip()

    @mock.patch('dnstwister.repository.db', patches.SimpleKVDatabase())
    def test_feed_reading_is_tracked(self):
        """Tests that reading a feed is logged."""
        repository = dnstwister.repository

        domain = 'www.example.com'
        b64domain = base64.b64encode(domain)

        # Read dates are None by default
        read_date = repository.delta_report_last_read(domain)
        assert read_date is None

        # Registering a feed will update the read date
        self.app.get('/atom/{}'.format(b64domain)).follow()
        read_date = repository.delta_report_last_read(domain)
        assert type(read_date) is datetime.datetime

        # Manually set the date to an older date so we don't have to 'sleep'
        # in the test.
        repository.mark_delta_report_as_read(
            domain, datetime.datetime(2000, 1, 1, 0, 0, 0)
        )

        # Clear the webapp cache
        dnstwister.cache.clear()

        # Reading a feed will update the read date
        read_date = repository.delta_report_last_read(domain)
        self.app.get('/atom/{}'.format(b64domain)).follow()
        read_date2 = repository.delta_report_last_read(domain)

        assert read_date2 > read_date

    @mock.patch('dnstwister.repository.db', patches.SimpleKVDatabase())
    def test_unregister_tidies_database(self):
        """Tests that you can unregister domains."""
        repository = dnstwister.repository

        domain = 'www.example.com'
        b64domain = base64.b64encode(domain)

        assert not repository.is_domain_registered(domain)
        assert repository.db.data == {}

        self.app.get('/atom/{}'.format(b64domain)).follow()
        repository.update_delta_report(
            domain, {
                'new': [('www.examp1e.com', '127.0.0.1')],
                'updated': [],
                'deleted': [],
            },
        )

        assert repository.is_domain_registered(domain)
        assert repository.db.data != {}

        repository.unregister_domain(domain)

        assert not repository.is_domain_registered(domain)
        assert repository.db.data == {}
