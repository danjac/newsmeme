# -*- coding: utf-8 -*-
"""
    test_helpers.py
    ~~~~~~~~

    NewsMeme tests

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""

from datetime import datetime, timedelta

from newsmeme.helpers import timesince, domain, slugify

from tests import TestCase


class TestSlugify(TestCase):

    def test_slugify(self):

        assert slugify("hello, this is a test") == "hello-this-is-a-test"

class TestDomain(TestCase):

    def test_valid_domain(self):
        
        assert domain("http://reddit.com") == "reddit.com"

    def test_invalid_domain(self):

        assert domain("jkjkjkjkj") == ""
        

class TestTimeSince(TestCase):

    def test_years_ago(self):

        now = datetime.utcnow()
        three_years_ago = now - timedelta(days=365 * 3)
        assert timesince(three_years_ago) == "3 years ago"

    def test_year_ago(self):

        now = datetime.utcnow()
        three_years_ago = now - timedelta(days=365)
        assert timesince(three_years_ago) == "1 year ago"

    def test_months_ago(self):

        now = datetime.utcnow()
        six_months_ago = now - timedelta(days=30 * 6)
        assert timesince(six_months_ago) == "6 months ago"

    def test_minutes_ago(self):

        now = datetime.utcnow()
        five_minutes_ago = now - timedelta(seconds=(60 * 5) + 40)
        assert timesince(five_minutes_ago) == "5 minutes ago"
