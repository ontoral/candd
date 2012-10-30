#!/usr/bin/env python

import os
import argparse


def main():
    '''convert downloaded data files to Fidelity format'''
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', help='path where data files are stored',
                        nargs='?',
                        default=os.environ.get('TIAA_CREF_DD', os.getcwd()))
    parser.add_argument('-c', '--custodian', choices=['TC'], default='TC',
                        help='abbreviation for data file(s) provider')
    parser.add_argument('-f', '--filetype', choices=['sec', 'pri'],
                        action='append',
                        help='the extension of a filetype to convert')
    args = parser.parse_args()
    print args

if __name__ == '__main__':
    main()
