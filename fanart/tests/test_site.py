import sys

def test_homepage_title(browser, webapp_url):
    browser.get(webapp_url)
    assert browser.title
    assert browser.title.startswith('Česká PokéGalerie')

def test_homepage_h1(browser, webapp_url):
    browser.get(webapp_url)
    h1 = browser.find_element_by_css_selector('h1')
    assert h1.text
    assert h1.text.startswith('Česká PokéGalerie')
