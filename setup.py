import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()

requires = [
    'pyramid',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'sqlalchemy',
    'zope.sqlalchemy',
    'clevercss>=0.2.2.dev',
    'mako',
    ]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='fanart',
      version='0.0',
      description='fanart',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
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
      entry_points = """\
      [paste.app_factory]
      main = fanart:main
      """,
      paster_plugins=['pyramid'],
      )

