#!/usr/bin/env python

import os
import sys
import urllib
import datetime

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


def get_date(month, day, year):
    if month is None:
        return datetime.date.today()
    return datetime.date(year, month, day)


def get_quote(symbol, month=None, day=None, year=None):
    date = get_date(month, day, year)
    url_date = date.strftime(URL_FORMAT)
    base_url = 'http://bigcharts.marketwatch.com/historical/default.asp?symb={symbol}&closeDate={url_date}&'
    content = urllib.urlopen(base_url.format(**locals())).read()

    # instantiate the parser and feed it some HTML
    parser = PriceParser()
    parser.feed(content)
    price_date = date.strftime(DATE_FORMAT)
    print '{price_date} price for {symbol:8} = {parser.price:8.02f}'.format(**locals())

    return parser.price


def get_quotes(month=None, day=None, year=None, symbol_file='symbols.txt',
               download_dir=None):
    date = get_date(month, day, year)
    date_str = date.strftime(PC_FORMAT)
    quotes = []

    if not os.path.exists(symbol_file):
        return
    with file(symbol_file, 'r') as symbols:
        for symbol in symbols:
            symbol = symbol.strip()
            if not symbol or symbol.startswith('#'):
                continue
            price = get_quote(symbol, date.month, date.day, date.year)
            if price >= 0:
                entry = '{symbol:9}{price:>64.02f}{date_str}\n'.format(**locals())
                quotes.append(entry)

    if download_dir and os.path.exists(download_dir) and len(quotes):
        filename = 'fi{date_str}.pri'.format(**locals())
        outfile = os.path.join(download_dir, filename)
        print 'File: ' + outfile
        with file(outfile, 'w') as out:
            out.write(''.join(quotes))


if __name__ == '__main__':
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
        dt = datetime.date(year, month, day)

        # Locate symbol file and download directory
        symbols = raw_input('   Symbol file ({symbol_file}): '.format(**locals()))
        downloads = raw_input('   Download directory ({download_dir}): '.format(**locals()))
        symbol_file = symbols if len(symbols) else symbol_file
        download_dir = downloads if len(downloads) else download_dir

    get_quotes(dt.month, dt.day, dt.year, symbol_file, download_dir)
