# Encoding: UTF-8


import pytz
import colander
import deform

from fanart.markdown import convert as markdown2html

markdown2html

local_timezone = pytz.timezone('Europe/Prague')

formats = dict(
        date='%d. %m. %Y %H:%M',
        compact='%H:%M',
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


@colander.deferred
def _deferred_csrf_default(node, kw):
    return kw['request'].csrf_token


class FormSchema(colander.MappingSchema):
    csrft = colander.SchemaNode(
        colander.String(),
        default=_deferred_csrf_default,
        widget=deform.widget.HiddenWidget(),
    )

def a(request, *users, m='', f='a', other='/a', m_pl='i', f_pl='y'):
    """Helper for forming Czech past participles, which depend on gender
    """
    if not users:
        users = [request.user]
    if len(users) == 1:
        if users[0].gender == 'male':
            return m
        elif users[0].gender == 'female':
            return f
        else:
            return other
    else:
        if all(u.gender != 'male' for u in users):
            return f_pl
        else:
            return m_pl
