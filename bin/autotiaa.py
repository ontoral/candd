#!/usr/bin/env python

import os
import re
from zipfile import ZipFile

import mechanize


# URL = 'https://www.tiaa-cref.org/public/index.html'  # Unnecessary
URL = 'https://publictools.tiaa-cref.org/private/selfservices/sso/login.do?command=getUserId'
USER_ID = os.environ.get('TIAA_CREF_USER_ID', 'userid')
PASSWORD = os.environ.get('TIAA_CREF_PASSWORD', 'password')
SQA = os.environ.get('TIAA_CREF_SQA', 'sqa')
DD = os.environ.get('TIAA_CREF_DD', os.getcwd())


def download_current_data():
    # Create browser and log in
    print 'Attempting login...'
    browser = mechanize.Browser()
    browser.open(URL)
    browser.select_form(nr=0)
    browser['userId'] = USER_ID
    browser.submit()
    browser.select_form(nr=0)
    browser['password'] = PASSWORD
    browser['securityQuestionAnswer'] = SQA
    browser.submit()
    print 'login successful!'

    # Navigate to Current Data file
    print 'Starting download...'
    browser.follow_link(text='Client Data Download')
    browser.select_form(name='downloadCurrentFileZip')
    browser.submit()
    browser.select_form(name='downloadForm')
    browser.submit()
    print 'download complete!'

    regexp = re.compile('.*filename=(.*)')
    filename = regexp.findall(browser.response().info())[0]

    return browser.response().get_data(), filename


def main():
    # Download data and open as a zip archive
    data, filename = download_current_data()
    return

    with ZipFile(filename, 'w') as zipped:
        zipped.write(data)
    print 'Archive stored as', filename

    # Extract files with matching extensions
    with ZipFile(filename) as z:
        for f in z.namelist():
            if f.lower()[-3:] in ['pri', 'sec']:
                print '\textracting', f
                z.extract(f, path=DD)


if __name__ == '__main__':
    main()
