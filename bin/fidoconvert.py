#!/usr/bin/env python

import os
import datetime
import glob
import argparse

PC_DATE_FORMAT = '%m%d%y'


def convert_csv(infile, outfile, converter=None):
    '''General purpose .CSV file conversion engine.'''
    # Convert data
    print '{infile}  -->  {outfile}'.format(**locals())
    with file(infile, 'r') as src:
        with file(outfile, 'w') as dst:
            for line in src:
                values = line.split(',')
                conv = converter(**locals()) if converter else src
                dst.write(conv)
    return True


def convert_fixed(infile, outfile, fields, converter=None):
    '''General purpose fixed-width file conversion engine.'''
    # Convert data
    print '{infile}  -->  {outfile}'.format(**locals())
    with file(infile, 'r') as src:
        with file(outfile, 'w') as dst:
            for line in src:
                values = []
                for field in fields:
                    values.append(line[:field])
                    line = line[field:]
                conv = converter(**locals()) if converter else src
                dst.write(conv)
    return True


def get_fidelity_path_from_tiaa_cref(tc_path):
    '''Generates a Fidelity export file path from a TIAA-CREF file path.'''
    # Get date
    filename = os.path.basename(tc_path)
    date = get_date_from_tiaa_cref(filename)

    # Get output filename
    path = os.path.dirname(tc_path)
    ext = filename[-3:].lower()
    pc_datestr = date.strftime(PC_DATE_FORMAT)
    return os.path.join(path, 'fi{pc_datestr}.{ext}'.format(**locals()))


def get_date_from_tiaa_cref(tc_file):
    '''Parse export file date from TIAA-CREF filename.'''
    # Get date components
    yr = int(tc_file[2:4]) + 2000
    mo = int(tc_file[4:6])
    dy = int(tc_file[6:8])

    return datetime.date(yr, mo, dy)


def convert_tiaa_cref_sec_file(infile):
    '''Convert Securities export file from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def sec(values, **kwargs):
        symbol = values[0]
        sec_type = 'MF'
        desc = values[2][0:40]
        cusip = values[21]
        return '{sec_type}{symbol:9}{desc:40}{cusip:>9}  0.00\n'.format(**locals())

    return convert_csv(infile, outfile, sec)


def convert_tiaa_cref_pri_file(infile):
    '''Convert Prices export file from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def pri(values, outfile, **kwargs):
        symbol = values[0]
        price = float(values[3])
        pc_datestr = os.path.basename(outfile)[2:8]
        return '{symbol:58}{price:>15.07f}{pc_datestr}\n'.format(**locals())

    return convert_csv(infile, outfile, pri)


def main():
    '''convert downloaded data files to Fidelity format'''

    # The conversions, as available, by custodian
    conversions = {
        'TC': {
            'pri': ('[aA][dD]*.[pP][rR][iI]', convert_tiaa_cref_pri_file, 'bap'),
            'sec': ('[aA][dD]*.[sS][eE][cC]', convert_tiaa_cref_sec_file, 'bac'),
        }
    }

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?',
                        help='folder where data files are stored and converted',
                        default=os.environ.get('TIAA_CREF_DD', os.getcwd()))
    parser.add_argument('-c', '--custodian', choices=['TC'], default='TC',
                        help='abbreviation for data file(s) provider')
    parser.add_argument('-f', '--filetype', choices=['sec', 'pri'],
                        action='append',
                        help='the extension of a filetype to convert')
    args = parser.parse_args()
    if args.filetype is None:
        args.filetype = conversions[args.custodian].keys()

    for filetype in args.filetype:
        conversion = conversions[args.custodian][filetype]
        filenames = glob.glob(os.path.join(args.path, conversion[0]))
        for filename in filenames:
            conversion[1](filename)
            os.rename(filename, filename[:-3] + conversion[2])

if __name__ == '__main__':
    main()
