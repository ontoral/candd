#!/usr/bin/env python

import argparse
import datetime
import os
import sys
import urllib

from HTMLParser import HTMLParser


URL_FORMAT = '%m%%2F%d%%2F%Y'
DATE_FORMAT = '%m/%d/%Y'
PC_FORMAT = '%m%d%y'


tiaa_cref_dd = os.environ.get('TIAA_CREF_DD', os.getcwd())
csvfiles = {'cref3': os.path.join(tiaa_cref_dd, 'cref3.csv'),
            'cref5': os.path.join(tiaa_cref_dd, 'cref5.csv'), 
            'crefbond': os.path.join(tiaa_cref_dd, 'crefbond.csv'), 
            'crefglob': os.path.join(tiaa_cref_dd, 'crefglob.csv'), 
            'crefgrow': os.path.join(tiaa_cref_dd, 'crefgrow.csv'), 
            'crefilb': os.path.join(tiaa_cref_dd, 'crefilb.csv'), 
            'crefsoci': os.path.join(tiaa_cref_dd, 'crefsoci.csv'), 
            'crefstok': os.path.join(tiaa_cref_dd, 'crefstok.csv')} 

class PriceParser(HTMLParser):
    tag = None
    closing_price_found = False
    price = -1

    def handle_starttag(self, tag, attrs):
        self.tag = tag

    def handle_data(self, data):
        if self.tag == 'th':
            if data.strip() == 'Closing Price:':
                self.closing_price_found = True
        if self.tag == 'td' and self.closing_price_found:
            data = ''.join(data.strip().split(','))
            try:
                self.price = float(data)
            except ValueError:
                self.price = 0.0
            self.closing_price_found = False


def get_quote(symbol, dt=None):
    dt = datetime.date.today() if dt is None else dt
    url_date = dt.strftime(URL_FORMAT)
    csv_date = dt.strftime(DATE_FORMAT)
    base_url = 'http://bigcharts.marketwatch.com/historical/default.asp?symb={symbol}&closeDate={url_date}&'
    verbose = '{price_date} price for {symbol:8} = {parser.price:8.02f}'
    content = urllib.urlopen(base_url.format(**locals())).read()

    # instantiate the parser and feed it some HTML
    parser = PriceParser()
    parser.feed(content)
    price_date = dt.strftime(DATE_FORMAT)
    print verbose.format(**locals())

    # If price doesn't download look for it in local CSV files
    if parser.price < 0:
        csvfile = csvfiles.get(symbol.lower(), None)
        if csvfile is None:
            return parser.price
        print 'Checking', csvfile
        with open(csvfile, 'r') as data:
            for line in data:
                date, price, _ = line.split(',')            
                if date == csv_date:
                    parser.price = float(price[1:])
                    print verbose.format(**locals())
                    break

    return parser.price


def get_quotes(symbols, dt):
    quotes = []

    for symbol in symbols:
        price = get_quote(symbol, dt)
        if price >= 0:
            quotes.append((symbol, price))
            if symbol.lower() == 'agg':
                quotes.append(('AGGINDEX', price))

    return quotes


def read_symbol_file(symbol_file='symbols.txt'):
    symbols = []

    if os.path.exists(symbol_file):
        with open(symbol_file, 'r') as f:
            for symbol in f:
                symbol = symbol.strip()
                if symbol.startswith('#'):
                    symbol = ''
                if symbols != '':
                    symbols.append(symbol)

    return symbols


def write_quotes_file(quotes, filename, date_str):
    """Build a fixed width quotes file from a collection of symbols and prices."""
    if not quotes:
        return

    # Create and write quote entries
    fixed = '{symbol:9}{price:>64.02f}{date_str}'
    entries = [fixed.format(**locals()) for symbol, price in quotes]
    with open(filename, 'a') as out:
        out.write('\n'.join(entries) + '\n')


def download_date(symbols, dt, download_dir):
    quotes = get_quotes(symbols, dt)
    date_str = dt.strftime(PC_FORMAT)

    # Get output filename
    if not os.path.exists(download_dir):
        print 'Download directory does not exist.'
        return

    name = 'fi{date_str}.pri'.format(**locals())
    filename = os.path.join(download_dir, name)
    print 'File: ' + filename

    write_quotes_file(quotes, filename, date_str)


def from_quick_date(quick_date):
    month = int(quick_date[0:2])
    day = int(quick_date[2:4])
    year = int(quick_date[4:6])
    this_year = datetime.date.today().year % 100
    if year <= this_year:
        year += 2000
    else:
        year += 1900
    return datetime.date(year, month, day)


def daterange(start_date, end_date=None):
    if end_date is None:
        end_date = start_date + datetime.timedelta(1)

    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def main(args):
    symbol_file = os.environ.get('SYMBOL_FILE',
                                 os.path.join('..', 'symbols.txt'))
    download_dir = os.environ.get('PRICE_DD',
                                  os.path.join('..', 'supplemental-prices'))

    # Get date or date range
    if args.start_date is not None and args.end_date is not None:
        # Download a range
        start_date = from_quick_date(args.start_date)
        end_date = from_quick_date(args.end_date) + datetime.timedelta(1)
    elif args.start_date is not None or args.end_date is not None:
        print 'Invalid date range specified'
        return
    else:
        # Download a single date as a 1-day range of dates
        if args.date is not None:
            start_date = from_quick_date(args.date)
            print 'start_date', start_date
        elif args.daily:
            start_date = datetime.date.today()
        else:
            print 'Downloading historical prices:'
            # Get date
            month = int(raw_input('   Month (1-12): '))
            day = int(raw_input('   Day (1-31): '))
            year = int(raw_input('   Year (ex. 2012): ')) % 100
            this_year = datetime.date.today().year % 100
            if year <= this_year:
                year += 2000
            else:
                year += 1900
            start_date = datetime.date(year, month, day)
        end_date = None

    # Obtain symbols
    if args.symbols is not None:
        symbols = args.symbols.split(',')
    else:
        # Symbols not provided, find them from a file
        if args.symbol_file is not None:
            symbol_file = args.symbol_file
        elif not args.daily:
            symfile = raw_input('   Symbol file ({symbol_file}): '.format(**locals()))
            symbol_file = symfile if len(symfile) else symbol_file
        symbols = read_symbol_file(symbol_file)

    # Obtain download directory
    if args.download_dir is not None:
        download_dir = args.download_dir
    elif not args.daily:
        downdir = raw_input('   Download directory ({download_dir}): '.format(**locals()))
        download_dir = downdir if len(downdir) else download_dir

    for dt in daterange(start_date, end_date):
        if dt.weekday() >= 5:
            continue
        download_date(symbols, dt, download_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-a', '--daily', action='store_true', default=False,
                        help='perform automated standard daily download')
    parser.add_argument('-d', '--date',
                        help='single date to download prices')
    parser.add_argument('-s', '--start-date',
                        help='first date to download from a range of dates')
    parser.add_argument('-e', '--end-date',
                        help='last date to download from a range of dates')
    parser.add_argument('-y', '--symbols',
                        help='comma separated list of symbols to download')
    parser.add_argument('-f', '--symbol-file',
                        help='file containing a list of symbols (absolute)')
    parser.add_argument('-p', '--download-dir',
                        help='path to download location (absolute)')

    main(parser.parse_args())
