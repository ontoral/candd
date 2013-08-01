#!/usr/bin/env python

import os
import datetime
import glob
import argparse

PC_DATE_FORMAT = '%m%d%y'


def convert_csv(infile, outfile, converter=None, file=None):
    '''General purpose .CSV file conversion engine.'''
    # Convert data
    print '{infile}  -->  {outfile}'.format(**locals())
    with file or open(infile, 'r') as src:
        with open(outfile, 'w') as dst:
            for line in src:
                values = line.split(',')
                conv = converter(**locals()) if converter else src
                dst.write(conv)
    return True


def convert_fixed(infile, outfile, fields, converter=None, file=None):
    '''General purpose fixed-width file conversion engine.'''
    # Convert data
    print '{infile}  -->  {outfile}'.format(**locals())
    with file or open(infile, 'r') as src:
        with open(outfile, 'w') as dst:
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
    tc_file = os.path.basename(tc_path)
    yr = int(tc_file[2:4]) + 2000
    mo = int(tc_file[4:6])
    dy = int(tc_file[6:8])
    date = datetime.date(yr, mo, dy)

    # Get output filename
    path = os.path.dirname(tc_path)
    ext = tc_file[-3:].lower()
    pc_datestr = date.strftime(PC_DATE_FORMAT)
    filename = 'fi{pc_datestr}.{ext}'.format(**locals())

    return os.path.join(path, filename)


def convert_tiaa_cref_sec_file(infile, file=None):
    '''Convert Securities export (.SEC) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def sec(values, **kwargs):
        symbol = values[0]
        sec_type = 'MF'
        desc = values[2][0:40]
        cusip = values[21]
        output = '{sec_type}{symbol:9}{desc:40}{cusip:>9}  0.00\n'

        return output.format(**locals())

    return convert_csv(infile, outfile, sec, file)


def convert_tiaa_cref_pri_file(infile, file=None):
    '''Convert Prices export (.PRI) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def pri(values, outfile, **kwargs):
        symbol = values[0]
        price = float(values[3])
        pc_datestr = os.path.basename(outfile)[2:8]
        output = '{symbol:58}{price:>15.07f}{pc_datestr}\n'

        return output.format(**locals())

    return convert_csv(infile, outfile, pri, file)


def convert_tiaa_cref_pos_file(infile, file=None):
    '''Convert Reconciliation export (.POS) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def pos(values, outfile, **kwargs):
        acct_num = values[0]
        acct_type = values[1]
        sec_type = values[2]
        symbol = values[3]
        quantity = values[4]
        amount = values[5]
        output = '\n'

        return output.format(**locals())

    return convert_csv(infile, outfile, pos, file)


def convert_tiaa_cref_trd_file(infile, file=None):
    '''Conver Portfolio export (.TRD) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

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
        output = '{acct_num:11}{tacct_num:10} {full_name}\n'

        return output.format(**locals())

    def trd_acc(values, outfile, **kwargs):
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
        month = int(pc_datestr[:2])
        day = int(pc_datestr[2:4])
        year = 2000 + int(pc_datestr[4:])
        date_str = '{year:4d}{month:02d}{day:02d}'.format(**locals())
        output = ('{acct_num:14} {skip:16}{full_name:20}{skip:5}'
                  '{tacct_num:10}{skip:35}{date_str:12} FIFO N\n')

        return output.format(**locals())

    outfile = outfile[:-4] + '.nam'
    nam = convert_csv(infile, outfile, trd_nam, file)
    outfile = outfile[:-4] + '.acc'
    acc = convert_csv(infile, outfile, trd_acc, file)

    return nam and acc


def convert_tiaa_cref_trn_file(infile, file=None):
    '''Convert Transaction export (.TRN) from TIAA-CREF to Fidelity format.'''
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
        output = '\n'

        return output.format(**locals())

    return convert_csv(infile, outfile, trn, file)


def main():
    '''convert downloaded data files to Fidelity format'''

    # Small class to collect conversion details
    class Conversion(object):
        def __init__(self, glob_pattern, converter, backup_extension):
            self.glob_pattern = glob_pattern
            self.converter = converter
            self.backup_extension = backup_extension

        def convert_path(self, path, skip_backup=False):
            print 'Matching ' + self.glob_pattern
            filenames = glob.iglob(os.path.join(path, self.glob_pattern))
            if not skip_backup:
                print '\t', 'Backing up files to *.{0}'.format(self.backup_extension)
            for filename in filenames:
                self.converter(filename)
                if not skip_backup:
                    os.rename(filename, filename[:-3] + self.backup_extension)
            print '----'

    # The conversions, as available, by custodian
    custodians = {
        'tiaacref': {
            'pri': Conversion('[aA][dD]*.[pP][rR][iI]', convert_tiaa_cref_pri_file, 'bap'),
            'sec': Conversion('[aA][dD]*.[sS][eE][cC]', convert_tiaa_cref_sec_file, 'bac'),
#            'trd': Conversion('[aA][dD]*.[tT][rR][dD]', convert_tiaa_cref_trd_file, 'bcc'),
        }
    }

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?',
                        help='folder where data files are stored and converted',
                        default=os.environ.get('TIAA_CREF_DD', os.getcwd()))
    parser.add_argument('-c', '--custodian', choices=['tiaacref'], default='tiaacref',
                        help='abbreviation for data file(s) provider')
    parser.add_argument('-f', '--filetype', choices=['sec', 'pri'],  # , 'trd'],
                        action='append',
                        help='the extension of a filetype to convert')
    parser.add_argument('-s', '--skip-backup', action='store_true',
                        help='original files are not renamed after conversion')
    args = parser.parse_args()

    # Get the conversions from the chosen custodian
    conversions = custodians[args.custodian]

    # If no filetype is given, choose all filetypes for current custodian
    if args.filetype is None:
        args.filetype = conversions.iterkeys()

    # Convert each filetype
    for filetype in args.filetype:
        print 'Converting {0} files for custodian: {1}'.format(filetype, args.custodian)
        conversion = conversions[filetype]
        conversion.convert_path(args.path, args.skip_backup)

if __name__ == '__main__':
    main()
