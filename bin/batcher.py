#!/usr/bin/env python

# Standard libraries
import argparse
import datetime
import os

# Custom modules
import pricer


skips = ['1402', '1926', '1933', '1934', 'FRCMQ', 'KBS']

def noflow(data, download_dir=None):
    date = None
    symbols = None

    for line in data:
        if not line.startswith('Receipt'):
            continue
        new_date = line[16:24]
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

                symbols = [symbol for symbol in symbols if not symbol in skips]
                quotes = pricer.get_quotes(symbols, year, month, day)
                date_str = ''.join(date.split('/'))
                pricer.write_quotes_file(quotes, date_str, download_dir)

            date = new_date
            symbols = []
        symbols.append(line[26:42].strip())

def unpriced(data, download_dir=None):
    date = None
    symbols = None

    for line in data:
        new_date = line[:8]
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

                symbols = [symbol for symbol in symbols if not symbol in skips]
                quotes = pricer.get_quotes(symbols, year, month, day)
                date_str = ''.join(date.split('/'))
                pricer.write_quotes_file(quotes, date_str, download_dir)

            date = new_date
            symbols = []
        symbols.append(line[27:43].strip())

sections = ['Unpriced Securities',
            'Portfolios with Inception Date After Requested Date Range',
            'Cash Flows Exceeding  10.000% of Interval Beginning Value',
            'No Market Value for Flow',
            'Journal Entries',
            'Trades to None',
            'Unmanaged Asset Flows',
            'Beginning Interval Value does not match the ending value of the previous interval - Portfolio Level',
            'Beginning Interval Value does not match the ending value of the previous interval - Asset Class Level',
            'Invalid Computed Intervals']

functions = [unpriced,
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


def main(filename=None):
    if not filename:
        filename = 'batch status report.txt'
    download_dir = os.environ.get('PRICE_DD',
                                  os.path.join('..', 'supplemental-prices'))

    section = None

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
    parser.add_argument('filename', nargs='?',
                        help='batch status report stored as a text file')
    # parser.add_argument('-c', '--custodian', choices=['tiaacref'], default='tiaacref',
    #                     help='abbreviation for data file(s) provider')
    # parser.add_argument('-f', '--filetype', choices=['sec', 'pri'],  # , 'trd'],
    #                     action='append',
    #                     help='the extension of a filetype to convert')
    # parser.add_argument('-s', '--skip-backup', action='store_true',
    #                     help='original files are not renamed after conversion')
    args = parser.parse_args()

    main(args.filename)
