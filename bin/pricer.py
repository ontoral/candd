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


def get_date(year, month, day):
    if year is None:
        return datetime.date.today()
    return datetime.date(year, month, day)


def get_quote(symbol, year=None, month=None, day=None):
    date = get_date(year, month, day)
    url_date = date.strftime(URL_FORMAT)
    base_url = 'http://bigcharts.marketwatch.com/historical/default.asp?symb={symbol}&closeDate={url_date}&'
    content = urllib.urlopen(base_url.format(**locals())).read()

    # instantiate the parser and feed it some HTML
    parser = PriceParser()
    parser.feed(content)
    price_date = date.strftime(DATE_FORMAT)
    print '{price_date} price for {symbol:8} = {parser.price:8.02f}'.format(**locals())

    return parser.price


def get_quotes(symbols, year=None, month=None, day=None):
    quotes = []

    for symbol in symbols:
        price = get_quote(symbol, year, month, day)
        if price >= 0:
            quotes.append((symbol, price))

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


def write_quotes_file(quotes, date_str, download_dir):
    """Build a fixed width quotes file from a collection of symbols and prices."""
    if not os.path.exists(download_dir):
        print 'Download directory does not exist.'
        return

    if not quotes:
        return

    # Get output filename
    filename = 'fi{date_str}.pri'.format(**locals())
    outfile = os.path.join(download_dir, filename)
    print 'File: ' + outfile

    # Create and write quote entries
    entries = ['{symbol:9}{price:>64.02f}{date_str}'.format(**locals()) for symbol, price in quotes]
    with file(outfile, 'a') as out:
        out.write('\n'.join(entries))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)

    symbol_file = os.environ.get('SYMBOL_FILE',
                                 os.path.join('..', 'symbols.txt'))
    download_dir = os.environ.get('PRICE_DD',
                                  os.path.join('..', 'supplemental-prices'))

    if len(sys.argv) == 2:
        if sys.argv[1] == 'daily':
            dt = datetime.date.today()
    else:
        print 'Downloading historical prices:'
        # Get date
        month = int(raw_input('   Month (1-12): '))
        day = int(raw_input('   Day (1-31): '))
        year = int(raw_input('   Year (ex. 2012): '))
        this_year = datetime.date.today().year
        if year % 100 <= this_year % 100:
            year += 2000
        else:
            year += 1900
        dt = datetime.date(year, month, day)
        date_str = dt.strftime(PC_FORMAT)

        # Locate symbol file and download directory
        symbols = raw_input('   Symbol file ({symbol_file}): '.format(**locals()))
        downloads = raw_input('   Download directory ({download_dir}): '.format(**locals()))
        symbol_file = symbols if len(symbols) else symbol_file
        download_dir = downloads if len(downloads) else download_dir

    symbols = read_symbol_file(symbol_file)
    quotes = get_quotes(symbols, year, month, day)
    write_quotes_file(quotes, date_str, download_dir)
