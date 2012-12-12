#!/usr/bin/env python

import os
import csv
import glob


PATH = '.'

class SchwabDialect(csv.Dialect):
    def __init__(self):
        self.delimiter = ','
        self.lineterminator = '\r\n'
        self.quotechar = '"'
        self.quoting = csv.QUOTE_ALL


