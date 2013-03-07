# Encoding: UTF-8


import os

import yaml

from fanart.models import NewsItem

def import_news(session):
    path = os.path.join(os.path.dirname(__file__), 'old_news.yaml')
    items = yaml.safe_load(open(path))
    for item in items:
        del item['reporter'] # XXX
        session.add(NewsItem(**item))
    session.commit()

    # XXX: WikiLinks - [[soutěž:1|tady]], [[Sheer Cold]]
    # XXX: Localipersonalization: {{a}}
    # XXX: Users: [[@Teysa]]
    # XXX: Site links: [blabla](pravidla)
    # XXX: yena-karty
