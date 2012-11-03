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
    '''Convert Securities export file (.SEC) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def sec(values, **kwargs):
        symbol = values[0]
        sec_type = 'MF'
        desc = values[2][0:40]
        cusip = values[21]
        return '{sec_type}{symbol:9}{desc:40}{cusip:>9}  0.00\n'.format(**locals())

    return convert_csv(infile, outfile, sec)


def convert_tiaa_cref_pri_file(infile):
    '''Convert Prices export file (.PRI) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def pri(values, outfile, **kwargs):
        symbol = values[0]
        price = float(values[3])
        pc_datestr = os.path.basename(outfile)[2:8]
        return '{symbol:58}{price:>15.07f}{pc_datestr}\n'.format(**locals())

    return convert_csv(infile, outfile, pri)


def convert_tiaa_cref_pos_file(infile):
    '''Convert Reconciliation export file (.POS) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def pos(values, outfile, **kwargs):
        acct_num = values[0]
        acct_type = values[1]
        sec_type = values[2]
        symbol = values[3]
        quantity = values[4]
        amount = values[5]
        return '\n'.format(**locals())

    return convert_csv(infile, outfile, pos)


def convert_tiaa_cref_trd_file(infile):
    '''Conver Portfolio export file (.TRD) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)
    namfile = outfile[:-4] + '.nam'
    accfile = outfile[:-4] + '.acc'

    def trd_nam(values, **kwargs):
        # broker = values[0]            # Not used
        last_name = values[1]
        first_name = values[2]
        full_name = '{first_name} {last_name}'.format(**locals())
        # Not sent by TIAA-CREF
        # street = values[3]            # Not sent by TIAA-CREF
        # address_2 = values[4]         # Not sent by TIAA-CREF
        # address_3 = values[5]         # Not sent by TIAA-CREF
        # address_4 = values[6]         # Not sent by TIAA-CREF
        # address_5 = values[7]         # Not sent by TIAA-CREF
        # address_6 = values[8]         # Not sent by TIAA-CREF
        # city = values[9]              # Not sent by TIAA-CREF
        # state = values[10]            # Not sent by TIAA-CREF
        # zip_code  = values[11]        # Not used
        tax_id = values[12]
        tax_id4 = tax_id[-4:]
        initials = first_name[0] + last_name[0]
        acct_num = 'TCX{tax_id4}{initials}'.format(**locals())
        tacct_num = 'F{acct_num}'.format(**locals())
        # acct_num = values[13]         # Not used
        # advisor_id = values[14]       # Not sent by TIAA-CREF
        # taxable  = values[15]         # Not used
        line = '{acct_num:11}{tacct_num:10} {full_name}\n'
        return line.format(**locals())

    def trd_acc(values, accfile, **kwargs):
        skip = ''
        # broker = values[0]
        last_name = values[1]
        first_name = values[2]
        full_name = '{first_name} {last_name}'.format(**locals())
        # street = values[3]
        # address_2 = values[4]
        # address_3 = values[5]
        # address_4 = values[6]
        # address_5 = values[7]
        # address_6 = values[8]
        # city = values[9]
        # state = values[10]
        # zip_code  = values[11]
        tax_id = values[12]
        tax_id4 = tax_id[-4:]
        initials = first_name[0] + last_name[0]
        acct_num = 'TCX{tax_id4}{initials}'.format(**locals())
        tacct_num = 'F{acct_num}'.format(**locals())
        # acct_num = values[13]
        # advisor_id = values[14]
        # taxable  = values[15]
        pc_datestr = os.path.basename(outfile)[2:8]
        day = int(pc_datestr[:2])
        month = int(pc_datestr[2:4])
        year = 2000 + int(pc_datestr[4:])
        date_str = '{year:4d}{month:2d}{day:2d}'.format(**locals())
        line = '{acct_num:14} {skip:16}{full_name:20}{skip:5}{tacct_num:10}{registration:24}{skip:6}{date_str:12} FIFO N\n'
        return line.format(**locals())

    nam = convert_csv(infile, namfile, trd_nam)
    acc = convert_csv(infile, accfile, trd_acc)
    return nam and acc


def convert_tiaa_cref_trn_file(infile):
    '''Convert Transaction export file (.TRN) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def trn(values, outfile, **kwargs):
        broker = values[0]
        # values[1] not used
        acct_num = values[2]
        trans_code = values[3]
        cancel = values[4]
        symbol = values[5]
        sec_code = values[6]
        trade_date = values[7]
        quantity = values[8]
        net_amount = values[9]
        gross_amount = values[10]
        broker_fee = values[11]
        other_fee = values[12]
        settle_date = values[13]
        from_to = values[14]
        # values[15] not used
        interest = values[16]
        comment = values[17]
        return '\n'.format(**locals())

    return convert_csv(infile, outfile, trn)


def main():
    '''convert downloaded data files to Fidelity format'''

    # The conversions, as available, by custodian
    conversions = {
        'TC': {
            'pri': ('[aA][dD]*.[pP][rR][iI]', convert_tiaa_cref_pri_file, 'bap'),
            'sec': ('[aA][dD]*.[sS][eE][cC]', convert_tiaa_cref_sec_file, 'bac'),
            'trd': ('[aA][dD]*.[tT][rR][dD]', convert_tiaa_cref_trd_file, 'bcc'),
        }
    }

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?',
                        help='folder where data files are stored and converted',
                        default=os.environ.get('TIAA_CREF_DD', os.getcwd()))
    parser.add_argument('-c', '--custodian', choices=['TC'], default='TC',
                        help='abbreviation for data file(s) provider')
    parser.add_argument('-f', '--filetype', choices=['sec', 'pri', 'trd'],
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
