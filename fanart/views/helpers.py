# Encoding: UTF-8


import datetime
import pytz

from fanart.markdown import convert as markdown2html

local_timezone = pytz.timezone('Europe/Prague')

formats = dict(
        date='%d. %m. %Y %H:%M',
    )

class FormattedDate(object):
    def __init__(self, date, format, pubdate=False):
        assert '"' not in format
        self.format = format
        self.utc_date = date
        self.local_date = pytz.utc.localize(date).astimezone(local_timezone)
        print(self.utc_date, self.local_date)
        self.pubdate = pubdate

    def __unicode__(self):
        return self.local_date.strftime(formats[self.format])
    __str__ = __unicode__

    def __html__(self):
        attribs = ['data-dateformat="%s"' % self.format]
        if self.pubdate:
            attribs.append(' pubdate="pubdate"')
        return '<time datetime="%sZ" %s>%s</time>' % (
                self.utc_date.isoformat(), ' '.join(attribs), self)

def format_date(date, **kwargs):
    kwargs.setdefault('format', 'date')
    return FormattedDate(date, **kwargs)
