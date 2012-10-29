#!/usr/bin/env python

import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='convert downloaded data files to Fidelity format')
    parser.add_argument('folder', help='path where data files are stored',
    					nargs='?',
                        default=os.environ.get('TIAA_CREF_DD', os.getcwd()))
    parser.add_argument('-c', '--custodian', help='abbreviation for data file(s) provider',
                        choices=['TC'], default='TC')
    parser.add_argument('-f', '--filetype', help='the extension of a filetype to convert',
                        choices=['sec', 'pri'], action='append') #, default=['sec', 'pri'])
    args = parser.parse_args()
    print args

if __name__ == '__main__':
	main()