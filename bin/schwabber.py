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

trans = os.path.join(os.environ.get('SCHWAB_DD', SCHWAB_DD),
                     '*_Transactions_*.CSV')
pos = os.path.join(os.environ.get('SCHWAB_DD', SCHWAB_DD),
                   '*_Positions_*.CSV')

def files_handler(path):
    for tt in glob.iglob(path):
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

files_handler(trans)
files_handler(pos)

