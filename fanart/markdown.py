# Encoding: UTF-8


import markdown
from markdown.inlinepatterns import DoubleTagPattern, SimpleTagPattern
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import fenced_code, def_list, tables, abbr, nl2br
from fanart.thirdparty import urlize, mdx_downheader, wikilinks


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
# Also, have these only start and end at word boundaries
engine.inlinePatterns["strong_em"] = DoubleTagPattern(
        r'\b(\*{6}|_{3})(.+?)\2\b', 'strong,em')
engine.inlinePatterns["strong"] = SimpleTagPattern(
        r'\b(\*{4}|_{2})(.+?)\2\b', 'strong')
engine.inlinePatterns["emphasis"] = SimpleTagPattern(
        r'\b(\*{2})([^\*{2}]+)\2\b', 'em')
engine.inlinePatterns["emphasis2"] = SimpleTagPattern(
        r'\b(_)(.+?)\2\b', 'em')

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
        sig = markdown.util.etree.SubElement(parent, 'div')
        sig.set('class', 'signature')
        sig.text = '—' + block.lstrip('~')

engine.parser.blockprocessors.add('signature', CodeBlockProcessor(engine.parser), '>code')

class MarkdownResultString(str):
    def __html__(self):
        return self

# And the actual function to call it all
def convert(source):
    if source:
        return MarkdownResultString(engine.convert(source))
    else:
        return ''
