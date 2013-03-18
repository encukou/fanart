# Encoding: UTF-8


import re

import markdown
from markdown.inlinepatterns import (Pattern, DoubleTagPattern,
        SimpleTagPattern, HtmlPattern)
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import headerid, fenced_code, def_list, tables, abbr, nl2br
from fanart.thirdparty import urlize, mdx_downheader, wikilinks

from pyramid.response import Response
from pyramid import httpexceptions

def build_url(label, base, end):
    # XXX: URLs for Wikilinks
    return None

def make_extension(module, **kwargs):
    return module.makeExtension(list(kwargs.items()))

engine = markdown.Markdown(safe_mode='escape', extensions=[
        # Convert \n to a line break (as most web-form-based Markdown flavors do)
        make_extension(nl2br),
        # Now the "Markdown Extra" extensions:
        # 1) Fenced code blocks. Noy really useful here but pretty cool.
        make_extension(fenced_code),
        # 2) Footnotes -- also not that useful, plus they're not localized and they produce non-unique IDs
        # 3) HeaderID -- don't want that in comments!
        # 4) Definition lists. Those are cool (though not terribly useful, I guess).
        make_extension(def_list),
        # 5) Tables. Those are cool as well (though also not too useful).
        make_extension(tables),
        # 6) Abbreviations. Nice and weird-looking.
        make_extension(abbr),
        # Now URLize: a must-have for the web!
        urlize.makeExtension(),
        # Downheader 3 times, so we start with <h4>
        mdx_downheader.makeExtension(),
        mdx_downheader.makeExtension(),
        mdx_downheader.makeExtension(),
        # And lastly, Fanart's own flavor of WikiLinks.
        wikilinks.makeExtension(list(dict(build_url=build_url).items())),
    ])

# Now, since `*hug*` or `*sigh*` just look **bad** in italics and without the
# asterisks, have **italics**, ****bold**** and ******bold italics******.
# Underscores will work as asterisks did.
engine.inlinePatterns["strong_em"] = DoubleTagPattern(
        r'(\*{6}|_{3})(.+?)\2', 'strong,em')
engine.inlinePatterns["strong"] = SimpleTagPattern(
        r'(\*{4}|_{2})(.+?)\2', 'strong')
engine.inlinePatterns["emphasis"] = SimpleTagPattern(
        r'(\*{2})([^\*{2}]+)\2', 'em')
engine.inlinePatterns["emphasis2"] = SimpleTagPattern(
        r'(_)(.+?)\2', 'em')

# Allow the <b>, <u> and <i> tags – legacy syntax users are used to
html_index = engine.inlinePatterns.index('link')
for tag in 'bui':
    engine.inlinePatterns.insert(html_index, 'html_' + tag, SimpleTagPattern(
            r'(<{0}>)(.+?)</{0}>'.format(tag), tag))

# Signatures: ~~block
class CodeBlockProcessor(BlockProcessor):
    """ Process code blocks. """

    def test(self, parent, block):
        return block.startswith('~~')

    def run(self, parent, blocks):
        block = blocks.pop(0)
        print(block)
        sig = markdown.etree.SubElement(parent, 'div')
        sig.set('class', 'signature')
        sig.text = '—' + block.lstrip('~')

engine.parser.blockprocessors.add('signature', CodeBlockProcessor(engine.parser), '>code')

class MarkdownResultString(str):
    def __html__(self):
        return self

# And the actual function to call it all
def convert(source):
    return MarkdownResultString(engine.convert(source))
