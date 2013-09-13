#!/usr/bin/env python

'''Process TIAA-CREF export archives to Fidelity format.

Locate, open, extract, and convert files in TIAA-CREF exports (.zip)
to Fidelity format, for direct use in PortfolioCenter interface. Afterwards
export is added to a permanent archive.'''

# Standard library modules
import argparse
import glob
import os
import re
from zipfile import ZipFile, ZIP_DEFLATED

# Custom modules
import fidoconvert


def main(source=None, destination=None):
    # Use directories from environment vars if none are given
    if source is None:
        source = os.environ.get('DOWNLOADS', os.getcwd())
    if destination is None:
        destination = os.environ.get('TIAA_CREF_DD', os.getcwd())

    # Match and convert supported file types
    regexp = re.compile('.*SEC$|.*PRI$')
    converters = {'PRI': fidoconvert.convert_tiaa_cref_pri_file,
                  'SEC': fidoconvert.convert_tiaa_cref_sec_file}

    # Find new archives and long-term storage
    archives = glob.glob(os.path.join(source, 'TIAA-CREF*.zip'))
    storage = os.path.join(destination, 'archives.zip')

    # Inspect any archives found, process supported files, and store long-term
    for archive in archives:
        # Open each archive and translate relevant files
        creffile = ZipFile(archive)
        for name in creffile.namelist():
            if regexp.match(name):
                # Use file extension to determine conversion
                converter = converters[name[-3:]]
                converter(os.path.join(destination, name), creffile.open(name)) 

        # Store archive in long-term storage and delete
        with ZipFile(storage, 'a') as longterm:
            longterm.write(archive, arcname=os.path.basename(archive),
                           compress_type=ZIP_DEFLATED)
        try:
            os.remove(archive)
        except OSError:
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?',
                        help='location of TIAA-CREF zip file(s)')
    parser.add_argument('destination', nargs='?',
                        help='location of extracted files')
    args = parser.parse_args()

    main(args.source, args.destination)

