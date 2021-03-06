import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()

requires = [
    'pyramid',
    'pyramid-tm',
    'pyramid-debugtoolbar',
    'waitress',
    'pyramid-beaker',
    'sqlalchemy',
    'clevercss>=0.2.2.dev',
    'mako',
    'deform',
    'py3k-bcrypt',
    'unidecode',
    'markdown',
    'pytz',
    'pyyaml',
    'iso8601',
    'dogpile.cache',
    ]

if sys.version_info[:3] < (3, 3):
    raise SystemError('Python 3.3+ required')

setup_args = dict(name='fanart',
    version='0.0',
    description='fanart',
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.3",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
    author='Petr Viktorin',
    author_email='encukou@gmail.com',
    url='',
    keywords='web pylons pyramid',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires = requires,
    tests_require = requires,
    test_suite="fanart",
    entry_points = {
        'paste.app_factory':
            ['main = fanart.wsgi_app:main'],
        'console_scripts':
            ['fanart = fanart.cli:entry_point'],
        }
)

if __name__ == '__main__':
    setup(**setup_args)
