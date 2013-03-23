A small community fanart site

Prerequisites:
- Python 3.3+
- Python packages: Pyramid, Mako, SQLAlchemy, ...
    see setup.py or requirements.txt
- ImageMagick for image manipulation
- PostgreSQL for the database (Or SQLite for testing. MySQL won't work.)
- Selenium for browser testing

Structure:
models/ - a SQLAlchemy database model: tables and relations and not much else
backend/ - a higher-level interface to the model: app logic, access control
static/ - static images, scripts, etc.
tasks/ - worker jobs
templates/ - Mako & CCSS templates
tests/ - the test suite
thirdparty/ - mostly Markdown plugins, changes here weren't upstreamed (yet)
views/ - the web app: routing & presentation
