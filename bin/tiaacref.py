#!/usr/bin/env python

'''Process TIAA-CREF export archives to Fidelity format.

Locate, open, extract, and convert files in TIAA-CREF exports (.zip)
to Fidelity format, for direct use in PortfolioCenter interface. Afterwards
export is added to a permanent archive.'''

# Standard library modules
import argparse
from datetime import datetime
import glob
import os
import re
from zipfile import ZipFile

# Other modules
import fidoconvert
import mechanize


URL = 'https://publictools.tiaa-cref.org/private/selfservices/sso/login.do?command=getUserId'
USER_ID = os.environ.get('TIAA_CREF_USER_ID', 'userid')
PASSWORD = os.environ.get('TIAA_CREF_PASSWORD', 'password')
SQA = os.environ.get('TIAA_CREF_SQA', 'sqa')

# Match and convert supported file types
EXTENSION_RE = '.*SEC$|.*PRI$'
CONVERTERS = {'PRI': fidoconvert.convert_tiaa_cref_pri_file,
              'SEC': fidoconvert.convert_tiaa_cref_sec_file}


def download_current_data():
    """For automated daily download of TIAA-CREF data files.

    Create a software browser via mechanize, then fill and submit
    the forms required to download the most current file posted on
    the TC website."""

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

    # Find filename in response info, or simulate
    filename_re = re.compile('.*filename=(.*)')
    header = str(browser.response().info())
    filename_match = filename_re.findall(header)
    if filename_match:
        filename = filename_match[0].strip()
    else:
        # Same as TIAA-CREF format, with added --
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = 'TIAA-CREF---{0}.zip'.format(stamp)

    return browser.response().get_data(), filename


def main(daily=False, source=None, destination=None):
    # Use directories from environment vars if none are given
    if source is None:
        source = os.environ.get('DOWNLOADS', os.getcwd())
    if destination is None:
        destination = os.environ.get('TIAA_CREF_DD', os.getcwd())
    archive_storage = os.path.join(destination, 'archives.zip')

    # Daily download checks TC website, otherwise local directory is checked
    if daily:
        current_data, filename = download_current_data()

        # Create an archive from web downloaded data
        filename = os.path.join(source, filename)
        with open(filename, 'w+t') as datafile:
            datafile.write(current_data)

        archives = [filename]
    else:
        # Find new archives
        archives = glob.glob(os.path.join(source, 'TIAA-CREF*.zip'))

    # Match file extensions with regexp
    extension_re = re.compile(EXTENSION_RE)

    # Inspect any archives found, process supported files, and store long-term
    for archive in archives:
        # Open each archive and translate relevant files
        with ZipFile(archive) as zipped_data:
            for name in zipped_data.namelist():
                name = name.upper()
                if extension_re.match(name):
                    # Use file extension to determine conversion
                    extension = name[-3:]
                    converter = CONVERTERS[extension]
                    converter(os.path.join(destination, name), zipped_data.open(name))

        # Store archive in long-term storage and (attempt to) delete
        with ZipFile(archive_storage, 'a') as zipped_archive:
            zipped_archive.write(archive, arcname=os.path.basename(archive))
        try:
            os.remove(archive)
        except OSError:
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-a', '--daily', action='store_true', default=False,
                        help='perform automated download of current data')
    parser.add_argument('source', nargs='?',
                        help='location of TIAA-CREF zip file(s)')
    parser.add_argument('destination', nargs='?',
                        help='location of extracted files')
    args = parser.parse_args()

    main(args.daily, args.source, args.destination)
