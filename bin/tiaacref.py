#!/usr/bin/env python

"""Read and respond to issues in a Batch Status Report.

Batch calculation of intervals in PortfolioCenter generates a Batch Status
Report (BSR). Use this command to generate interface files to resolve BSR
concerns."""

# Standard libraries
import argparse
import datetime
import glob
import os
import re
import zipfile

# Custom modules
import fidoconvert
import pricer


# Hand entered list of symbols that should be ignored
# These symbols find erroneous historical prices
skip_symbols = ['1402', '1926', '1933', '1934', 'FRCMQ', 'KBS']


def download_missing_prices(data, download_dir, date_start=0, symbol_start=8,
                            pattern=None):
    """Download historical prices based on Batch Status Report.

    Inputs:
        data         - List of strings from BSR
        download_dir - Destination for new price files
        date_start   - Column where date is located in lines (mm/dd/yy)
        symbol_start - Column where symbol is located in lines
        patter       - Optional RegExp to identify lines that need parsing"""
    date = None
    symbols = set()

    for line in data:
        # If a pattern is provided, only use matching lines
        if pattern is not None:
            if not re.compile(pattern).match(line):
                continue

        new_date = line[date_start:date_start + 8]
        if new_date != date:
            if date:
                m, d, y = date.split('/')
                year = int(y) % 100
                if year <= datetime.date.today().year % 100:
                    year += 2000
                else:
                    year += 1900
                month = int(m)
                day = int(d)

                quotes = pricer.get_quotes(symbols, year, month, day)
                date_str = ''.join(date.split('/'))
                pricer.write_quotes_file(quotes, date_str, download_dir)

            date = new_date
            symbols = set()

        symbol = line[symbol_start:symbol_start + 16].strip()
        if symbol not in skip_symbols:
            symbols.add(symbol)


def noflow(data, download_dir):
    """'No Market Value for Flow' handler

    "Receipt of Securities" with no price info get downloaded."""
    download_missing_prices(data, download_dir, 16, 26, '^Receipt|^Transfer.*')


def unpriced(data, download_dir=None):
    """'Unprices Securities' handler

    Missing price file or symbols not included in file get downloaded."""
    download_missing_prices(data, download_dir, symbol_start=27)


def main2(filename, download_dir=None):
    # Create a function lookup dict to handle sections of BSR
    sections = ['Missing Price Files',
                'Unpriced Securities',
                'Portfolios with Inception Date After Requested Date Range',
                'No Inception Date for Portfolio',
                'Cash Flows Exceeding  10.000% of Interval Beginning Value',
                'No Market Value for Flow',
                'Journal Entries',
                'Trades to None',
                'Inception Flows for Group Members',
                'Unmanaged Asset Flows',
                'Beginning Interval Value does not match the ending value of the previous interval - Portfolio Level',
                'Beginning Interval Value does not match the ending value of the previous interval - Asset Class Level',
                'Invalid Computed Intervals']
    functions = [None,
                 None,
                 None,
                 None,
                 None,
                 noflow,
                 None,
                 None,
                 None,
                 None,
                 None,
                 None,
                 None]
    handlers = dict(zip(sections, functions))

    # Ensure download directory
    if not download_dir:
        download_dir = os.environ.get('PRICE_DD',
                                      os.path.join('..', 'supplemental-prices'))

    section = None

    # Process BSR line by line, and section by section
    with open(filename, 'r') as f:
        while f:
            # Read and clean 1 line at a time
            line = f.readline()
            if line == '':
                break
            else:
                line = line.strip()

            # Look for section headers and collect data
            if line in sections:
                section = line
                print 'Entering section:', line
                f.readline()  # Eliminate a blank line
                header = f.readline().strip()
                while header[0] != '-':
                    print '\t', header
                    header = f.readline().strip()

                # Section header found, collect data
                data = []
                while line != '':
                    line = f.readline().strip()
                    if line:
                        data.append(line)

            # Handle the end of a section
            if section and line == '':
                print '\t', len(data), 'lines'
                func = handlers[section]
                if func:
                    func(data, download_dir)
                print 'Exiting...\n'
                section = None


def main(source, destination):
    # Use directory from environment vars if none is given
    if destination is None:
        destination = os.environ.get('TIAA_CREF_DD', os.getcwd())

    # Match and convert supported file types
    regexp = re.compile('.*SEC$|.*PRI$')
    converters = {'PRI': fidoconvert.convert_tiaa_cref_pri_file,
                  'SEC': fidoconvert.convert_tiaa_cref_sec_file}

    #print source
    #print destination

    # Find new archives and long-term storage
    archives = glob.glob(os.path.join(source, 'TIAA-CREF*.zip'))
    storage = os.path.join(destination, 'archives.zip')

    # Inspect any archives found, process supported files, and store long-term
    for archive in archives:
        # Open each archive and translate relevant files
        creffile = zipfile.ZipFile(archive)
        for name in creffile.namelist():
            if regexp.match(name):
                # Use file extension to determine conversion
                converter = converters[name[-3:]]
                converter(os.path.join(destination, name), creffile.open(name)) 

        # Store archive in long-term storage and delete
        with zipfile.ZipFile(storage, 'a') as longterm:
            longterm.write(archive, arcname=os.path.basename(archive),
                           compress_type=zipfile.ZIP_DEFLATED)
        try:
            os.remove(archive)
        except OSError:
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',
                        help='location of TIAA-CREF zip file(s)')
    parser.add_argument('destination', nargs='?',
                        help='location of extracted files')
    args = parser.parse_args()

    main(args.source, args.destination)

