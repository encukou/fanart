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

def test_create_user(browser, webapp_url, webapp_backend, Keys):
    browser.get(webapp_url)
    browser.find_element_by_link_text('Založit nový účet').click()
    field = browser.find_element_by_css_selector('.deform [name=user_name]')
    field.send_keys(Keys.CLEAR, 'new user')
    field = browser.find_element_by_css_selector('.deform [name=password]')
    field.send_keys(Keys.CLEAR, 'super*secret')
    field = browser.find_element_by_css_selector('.deform [name=password2]')
    field.send_keys(Keys.CLEAR, 'super*secret')
    field = browser.find_element_by_css_selector('.deform button.submit')
    field.click()

    assert {u.name for u in webapp_backend.users} == {'Test', 'new user'}
    assert webapp_backend.users['new user'].check_password('super*secret')
