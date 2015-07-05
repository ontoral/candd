#!/usr/bin/env python

import os
import csv
import glob
import re


SCHWAB_DD = '.'

class SchwabDialect(csv.Dialect):
    def __init__(self):
        self.delimiter = ','
        self.lineterminator = '\r\n'
        self.quotechar = '"'
        self.quoting = csv.QUOTE_ALL
csv.register_dialect('schwab_export', SchwabDialect())

schwab_dd = os.environ.get('SCHWAB_DD', SCHWAB_DD)
trans = '*Transactions*.CSV'
pos = '*Positions*.CSV'

def files_handler(path, pattern):
    for tt in glob.iglob(os.path.join(path, pattern)):
        with file(tt, 'r') as f:
            prefix = os.path.basename(tt).split('-')[0]
            if int(prefix) == 0:    # a closed account
                continue
            info = f.readline()
            acct_re = re.search('^.*XXXX(-[0-9]{4}).*', info)
            suffix = acct_re.groups()[0]
            account_num = prefix+suffix
            print account_num
            csv_reader = csv.reader(f, dialect='schwab_export')
            header = None
            for row in csv_reader:
                if not header:
                    header = row
                else:
                    if len(row) != len(header):
                        continue
                    d = dict(zip(header, row))
                    d['account'] = account_num
                    print d

def account_trans_to_date(path):
    dates = {}
    print os.path.join(path, trans)
    for acct in glob.iglob(os.path.join(path, trans)):
        with open(acct) as a:
            # Construct the account number from filename and contents
            prefix = os.path.basename(acct)[:4]
            line = a.readline()
            acct_re = re.search('^.*XXXX-([0-9]{4}).*', line)
            suffix = acct_re.groups()[0]
            account_num = '-'.join([prefix, suffix])
            #print account_num

            # Column headers
            junk = a.readline()

            # File data
            csv_reader = csv.reader(a)
            for row in csv_reader:
                if len(row) < 9:
                    continue
                trans_date = row[0][:10]
                row.append(account_num)
                if trans_date not in dates:
                    dates[trans_date] = []
                dates[trans_date].append(row)

    for dt in dates.iterkeys():
        parts = dt[:10].split('/')
        #print dt
        filename = 'cs' + parts[0] + parts[1] + dt[-2:] + '.trn.CSV'
        with open(filename, 'w') as out:
            csv_writer = csv.writer(out)
            csv_writer.writerows(dates[dt])

    print len(dates), '.trn files written by date.'


if __name__ == '__main__':
    #files_handler(schwab_dd, trans)
    #files_handler(schwab_dd, pos)
    account_trans_to_date(schwab_dd)

