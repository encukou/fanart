# Encoding: UTF-8
from __future__ import unicode_literals, division, absolute_import

import datetime
from pytz import timezone

from fanart.markdown import convert as markdown2html

local_timezone = timezone('Europe/Prague')

formats = dict(
        date='%d. %m. %Y',
    )

class FormattedDate(object):
    def __init__(self, date, format, pubdate=False):
        assert '"' not in format
        self.format = format
        self.date = local_timezone.localize(date)
        self.pubdate = pubdate

    def __unicode__(self):
        return self.date.strftime(formats[self.format])

    def __html__(self):
        attribs = ['data-dateformat="%s"' % self.format]
        if self.pubdate:
            attribs.append(' pubdate="pubdate"')
        return '<time datetime="%s" %s>%s</time>' % (
                self.date.isoformat(), ' '.join(attribs), self)

def format_date(date, **kwargs):
    kwargs.setdefault('format', 'date')
    return FormattedDate(date, **kwargs)
