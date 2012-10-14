import sys
import urllib
import datetime

from HTMLParser import HTMLParser

class MyHTMLParser(HTMLParser):
    tag = None
    price = -1
    def handle_starttag(self, tag, attrs):
        if tag == 'span' and ('class', 'pr') in attrs:
            self.tag = 'price'
    def handle_data(self, data):
        if self.tag == 'price' and data.strip():
            try:
                self.price = float(''.join(data.split(',')))
            except ValueError, e:
                self.price = 0.0
            self.tag = None


class MyHistoricalParser(HTMLParser):
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
            try:
                self.price = float(''.join(data.strip().split(',')))
            except ValueError, e:
                self.price = 0.0
            self.closing_price_found = False


def get_historical_quote(symbol, month, day, year):
    date = '%02d/%02d/%d' % (month, day, year)
    base_url = 'http://bigcharts.marketwatch.com/historical/default.asp?symb=%s&closeDate=%s&'
    content = urllib.urlopen(base_url % (symbol, date.replace('/', '%2F'))).read()

    # instantiate the parser and feed it some HTML
    parser = MyHistoricalParser()
    parser.feed(content)
    print '%s price for %s is %0.02f.' % (date, symbol, parser.price)

    return parser.price

def get_quote(symbol):
    base_url = 'http://finance.google.com/finance?q='
    content = urllib.urlopen(base_url+symbol).read()

    # instantiate the parser and feed it some HTML
    parser = MyHTMLParser()
    parser.feed(content)
    print 'Price for {0} is {1:0.02f}'.format(symbol, parser.price)

    return parser.price

def get_historical_quotes(month, day, year):
    quotes = []
    date_str = '{0:02}{1:02}{2:02}'.format(month, day, year % 1000)

    symbols = file('..\\symbols.txt', 'r')
    for symbol in symbols:
        symbol = symbol.strip()
        if not symbol or symbol.startswith('#'):
            continue
        price = get_historical_quote(symbol, month, day, year)
        entry = '{0:9}{1:>64.02f}{2}'.format(symbol, price, date_str)
##        print entry
        quotes.append(entry)

    filename = '..\\supplemental-prices\\fi{0}.pri'.format(date_str)
##    filename = 'fi%s.pri' % date_str
##    filename = '%d-%02d-%02d-prices.txt' % (year, month, day)
    print 'File: '+filename
    outfile = file(filename, 'w')
    outfile.write('\n'.join(quotes))

def get_quotes():
    quotes = []
    date_str = datetime.date.today().strftime('%m%d%y')

    symbols = file('..\\symbols.txt', 'r')
    for symbol in symbols:
        symbol = symbol.strip()
        if not symbol or symbol.startswith('#'):
            continue
        price = get_quote(symbol)
        entry = '{0:9}{1:>64.02f}{2}'.format(symbol, price, date_str)
##        print entry
        quotes.append(entry)

    filename = '..\\supplemental-prices\\fi{0}.pri'.format(date_str)
##    filename = str(datetime.datetime.now()).split()[0]+'-prices.txt'
    print 'File: '+filename
    outfile = file(filename, 'w')
    outfile.write('\n'.join(quotes))


if __name__ == '__main__':
##    with file('log.txt', 'w') as logfile:
##        logfile.write(str(sys.argv))

    if len(sys.argv) == 2:
        if sys.argv[1] == 'daily':
            get_quotes()
    else:
        print 'Downloading historical prices:'
        month = int(raw_input('   Month (1-12): '))
        day = int(raw_input('   Day (1-31): '))
        year = int(raw_input('   Year (ex. 2012): '))
        get_historical_quotes(month, day, year)

    # get_quote('goog')
    # get_quote('aapl')
    # get_quote('brkb')
    # get_quote('trrjx')
