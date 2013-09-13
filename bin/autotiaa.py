#!/usr/bin/env python

# Standard library imports
import os
import re
from StringIO import StringIO
from zipfile import ZipFile

# Other imports
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
    filename = regexp.findall(str(browser.response().info()))[0].strip()

    return browser.response().get_data(), filename


def main():
    # Download data and open as a zip archive
    data, filename = download_current_data()

    # Extract files with matching extensions
    with ZipFile(StringIO(data)) as zipped:
        for f in zipped.namelist():
            if f.lower()[-3:] in ['pri', 'sec']:
                print '\textracting', f
                zipped.extract(f, path=DD)

    # Add full download zip to permanent archive
    with ZipFile(os.path.join(DD, 'archives.zip'), 'a') as zipped:
        zipped.writestr(filename, data)
    print 'Archive stored as', filename

    from tiaacref import main as tc
    tc()


if __name__ == '__main__':
    main()
