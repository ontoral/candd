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
EXTENSION_RE = '.*INI$|.*SEC$|.*PRI$|.*TRD$|.*TRN$|.*POS$'
CONVERTERS = {'INI': fidoconvert.convert_tiaa_cref_ini_file,
              'SEC': fidoconvert.convert_tiaa_cref_sec_file,
              'PRI': fidoconvert.convert_tiaa_cref_pri_file,
              'TRD': fidoconvert.convert_tiaa_cref_trd_file,
              'TRN': fidoconvert.convert_tiaa_cref_trn_file,
              'POS': fidoconvert.convert_tiaa_cref_pos_file}


def tiaacref_login():
    """Log a web browser into TIAA-CREF.

    returns:
        browser: a mechanize web browser

    Create a software browser with mechanize, then login through
    primary and secondary authentication at TIAA-CREF."""

    # Create browser and log in
    browser = mechanize.Browser()
    browser.open(URL)
    browser.select_form(nr=0)
    browser['userId'] = USER_ID
    browser.submit()
    browser.select_form(nr=0)
    browser['password'] = PASSWORD
    browser['securityQuestionAnswer'] = SQA
    browser.submit()

    return browser


def download_current_data():
    """For automated daily download of TIAA-CREF data files.

    Fill and submit the forms required to download the most current
    file posted on the TC website."""

    # Create browser and log in
    print 'Attempting login...'
    browser = tiaacref_login()
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
    header = str(browser.response().info())
    match = re.search('.*filename=(.*\.zip)', header)
    if match:
        filename = match.group(1)
    else:
        # Same as TIAA-CREF format, with added --
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = 'TIAA-CREF-{0}.zip'.format(stamp)

    return browser.response().get_data(), filename


def main(daily=False, source=None, download_dir=None):
    # Use directories from environment vars if none are given
    if source is None:
        source = os.environ.get('DOWNLOADS', os.getcwd())
    if download_dir is None:
        download_dir = os.environ.get('TIAA_CREF_DD', os.getcwd())
    archive_storage = os.path.join(download_dir, 'archives.zip')

    # Daily download checks TC website, otherwise local directory is checked
    if daily:
        current_data, filename = download_current_data()

        # Create an archive from web downloaded data
        filename = os.path.join(source, filename)
        with open(filename, 'w+b') as datafile:
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
                    with open(os.path.join(download_dir, 'date.log'), 'a') as f:
                        f.write('{}: {}\n'.format(str(datetime.today().date()),
                                                  name))
                    # Use file extension to determine conversion
                    extension = name[-3:]
                    converter = CONVERTERS[extension]
                    converter(os.path.join(download_dir, name), zipped_data.open(name))

        # Store archive in long-term storage and (attempt to) delete
        with ZipFile(archive_storage, 'a') as zipped_archive:
            zipped_archive.write(archive, arcname=os.path.basename(archive))
        try:
            os.remove(archive)
        except OSError:
            pass

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-a', '--daily', action='store_true', default=False,
                        help='perform automated download of current data')
    parser.add_argument('-s', '--source',
                        help='location of TIAA-CREF zip file(s)')
    parser.add_argument('-d', '--destination',
                        help='location of extracted files')
    args = parser.parse_args()

    main(args.daily, args.source, args.destination)
