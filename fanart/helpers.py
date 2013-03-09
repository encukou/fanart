import io
import re

from unidecode import unidecode

def make_identifier(name):
    name = unidecode(name).lower()
    name = re.sub('[^a-z0-9]+', '-', name)
    return name.strip('-') or '-'

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
