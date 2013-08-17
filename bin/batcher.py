#!/usr/bin/env python

"""Read and respond to issues in a Batch Status Report.

Batch calculation of intervals in PortfolioCenter generates a Batch Status
Report (BSR). Use this command to generate interface files to resolve BSR
concerns."""

# Standard libraries
import argparse
import datetime
import os
import re

# Custom modules
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
    download_missing_prices(data, download_dir, 16, 26, '^Receipt.*')


def unpriced(data, download_dir=None):
    """'Unprices Securities' handler

    Missing price file or symbols not included in file get downloaded."""
    download_missing_prices(data, download_dir, symbol_start=27)


def main(filename, download_dir=None):
    # Create a function lookup dict to handle sections of BSR
    sections = ['Missing Price Files'
                'Unpriced Securities',
                'Portfolios with Inception Date After Requested Date Range',
                'Cash Flows Exceeding  10.000% of Interval Beginning Value',
                'No Market Value for Flow',
                'Journal Entries',
                'Trades to None',
                'Unmanaged Asset Flows',
                'Beginning Interval Value does not match the ending value of the previous interval - Portfolio Level',
                'Beginning Interval Value does not match the ending value of the previous interval - Asset Class Level',
                'Invalid Computed Intervals']
    functions = [None,
                 unpriced,
                 None,
                 None,
                 noflow,
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('filename', nargs=1,
                        help='batch status report stored as a text file')
    parser.add_argument('-d', '--download-directory', nargs='?',
                        help='destination for new price files')
    args = parser.parse_args()

    main(args.filename, args.download_directory)
