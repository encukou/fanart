# Encoding: UTF-8


from io import StringIO

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


class FileUploadTempStore(object):

    def __init__(self, request):
        self.request = request
        self.session = request.session

    def __setitem__(self, name, value):
        data = value.copy()
        try:
            fp = data['fp']
        except KeyError:
            pass
        else:
            data['fp'] = fp.read()
        try:
            self.session.uploads
        except AttributeError:
            self.session.uploads = {}
        self.session.uploads[name] = data

    def __getitem__(self, name):
        if name in self.session:
            try:
                data = self.session.uploads[name]
            except AttributeError:
                raise KeyError(name)
            rv_data = {}
            for key, value in data:
                if key == 'fp' and value is not None:
                    value = StringIO(value)
                rv_data[key] = value
            return rv_data
        else:
            raise KeyError(name)

    def __delitem__(self, name):
        del self.session[name]

    def __contains__(self, name):
        return name in self.session

    def get(self, name, default=None):
        try:
            self.__getitem__(name)
        except:
            return default

    def preview_url(self, name):
        return None
