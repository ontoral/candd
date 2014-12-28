#!/usr/bin/env python

import os
import datetime
import glob
import argparse
from subprocess import call

PC_DATE_FORMAT = '%m%d%y'


def convert_csv(infile, outfile, converter, file=None, mode='w'):
    '''General purpose .CSV file conversion engine.'''
    # Convert data
    print '{infile}  -->  {outfile}'.format(**locals())
    with file or open(infile, 'r') as src:
        output = []
        for line in src:
            # Get distinct values from line of input
            values = line.split(',')

            output.append(converter(**locals()))
                
    with open(outfile, mode) as dst:
        dst.write('\r\n'.join(output))
    call(['chown', 'Administrators', outfile])

    return True


def convert_fixed(infile, outfile, fields, converter, file=None, mode='w'):
    '''General purpose fixed-width file conversion engine.'''
    # Convert data
    print '{infile}  -->  {outfile}'.format(**locals())
    with file or open(infile, 'r') as src:
        output = []
        for line in src:
            # Get distinct values from line of input
            values = []
            for field in fields:
                values.append(line[:field])
                line = line[field:]

            output.append(converter(**locals()))

    with open(outfile, mode) as dst:
        dst.write('\r\n'.join(output))
    call(['chown', 'Administrators', outfile])

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
        output = '{sec_type}{symbol:9}{desc:40}{cusip:>9}  0.00'

        return output.format(**locals())

    return convert_csv(infile, outfile, sec, file)


def convert_tiaa_cref_pri_file(infile, file=None):
    '''Convert Prices export (.PRI) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def pri(values, outfile, **kwargs):
        symbol = values[0]
        price = float(values[3])
        pc_datestr = os.path.basename(outfile)[2:8]
        output = '{symbol:58}{price:>15.07f}{pc_datestr}'

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
        output = '\r\n'

        return output.format(**locals())

    return convert_csv(infile, outfile, pos, file)


def convert_tiaa_cref_trd_file(infile, file=None):
    '''Conver Portfolio export (.TRD) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def trd_nam(values, **kwargs):
        # broker = values[0] or 'TC'    # Not used
        last_name = values[1]
        first_name = values[2]
        # street = values[3]            # Not sent by TIAA-CREF
        # address_2 = values[4]         # Not sent by TIAA-CREF
        # address_3 = values[5]         # Not sent by TIAA-CREF
        # address_4 = values[6]         # Not sent by TIAA-CREF
        # address_5 = values[7]         # Not sent by TIAA-CREF
        # address_6 = values[8]         # Not sent by TIAA-CREF
        # city = values[9]              # Not sent by TIAA-CREF
        # state = values[10]            # Not sent by TIAA-CREF
        # zip_code  = values[11]        # Not sent by TIAA-CREF
        # tax_id = values[12] and ''
        acct_num = values[13][-6:] + values[13][:8]
        # advisor_id = values[14]       # Not sent by TIAA-CREF
        # taxable  = values[15]         # Not sent by TIAA-CREF
        # phone_num = values[16]        # Not sent by TIAA-CREF
        # fax_num = values[17]          # Not sent by TIAA-CREF
        # acct_type = values[18]        # Not sent by TIAA-CREF
        # objective = values[19]        # Not sent by TIAA-CREF
        # billing_acct = values[20]     # Not sent by TIAA-CREF
        # default_acct = values[21]     # Not sent by TIAA-CREF

        # Other values
        full_name = '{first_name} {last_name}'.format(**locals())[:48]
        tacct_num = 'TC{}'.format(values[13][:8])
        acct_num11 = acct_num[:11]

        output = '{acct_num11:11}{tacct_num:10} {full_name}'

        return output.format(**locals())

    def trd_acc(values, outfile, **kwargs):
        last_name = values[1]
        first_name = values[2]
        tax_id = values[12] and ''
        acct_num = values[13][-6:] + values[13][:8]
        taxable = values[15]
        acct_type = values[18][:24]

        # Other values
        full_name = '{first_name} {last_name}'.format(**locals())[:20]
        tacct_num = 'TC{}'.format(values[13][:8])
        pc_datestr = os.path.basename(outfile)[2:8]
        month = int(pc_datestr[:2])
        day = int(pc_datestr[2:4])
        year = 2000 + int(pc_datestr[4:])
        date_str = '{year:4d}{month:02d}{day:02d}'.format(**locals())
        cost_basis = 'FIFO'
        corp_indicator = 'N'

        output = ('{acct_num:14} {tax_id:11}     {full_name:20}     '
                  '{tacct_num:10}     {acct_type:24}      {date_str:12} '
                  '{cost_basis:4} {corp_indicator:1}')

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
        broker = values[0] and 'TC'
        # values[1] not used
        # TC Acct#: 'AAAAAAAA BBBBBB CCCCCC' -> PC Acct#: 'AAAAAAAACCCCCC'
        acct_num = values[2][-6:] + values[2][:8]
        trans_code = {'BUY': 'by',
                      'DEP': 'dp',
                      'DIV': 'dv',
                      'INT': 'in',
                      'SELL': 'sl',
                      'WITH': 'wd'}[values[3]]
        cancel = values[4]
        symbol = values[5].lower()
        sec_code = values[6]
        trade_date = values[7][:4] + values[7][-2:]  # Convert from MMDDYYYY
        quantity = float(values[8])
        net_amount = float(values[9])
        gross_amount = float(values[10] or '0')
        broker_fee = float(values[11] or '0')
        other_fee = float(values[12] or '0')
        settle_date = values[13] or trade_date
        from_to = values[14]
        # values[15] not used
        interest = float(values[16] or '0')
        comment = values[17]
        
        # Other values
        sec_type_code = 'mf'
        tk_code, tkc_desc = {'by': ('BOT', 'BOUGHT'),
                             'dp': ('DDP', 'DIRECT DEPOSIT'),
                             'dv': ('DIV', 'DIVIDEND'),
                             'in': ('INT', 'INTEREST'),
                             'sl': ('SLD', 'SOLD'),
                             'wd': ('ICP', 'CHECK PAID')}[trans_code]
        source = 'client' if trans_code in ['dp', 'wd'] else 'cash'
        if cancel == 'Y':
            trans_code = trans_code.upper()
        SEC_fee = 0.0
        option_symbol = ''
        order_action = ''
        output = ('{acct_num:14}{trans_code:2} {trade_date:6} '
                  '{sec_type_code:2} {symbol:9} {net_amount:>15.02f} {source:7} '
                  '{quantity:>15.05f} {broker:7} {broker_fee:>9.02f} {tk_code:4} '
                  '{tkc_desc:21} {other_fee:>16.04f} {SEC_fee:>16.04f} '
                  '{option_symbol:30} {settle_date:6} {order_action:20}')

        return output.format(**locals())

    return convert_csv(infile, outfile, trn, file, mode='a')


def convert_tiaa_cref_ini_file(infile, file=None):
    '''Convert Initial Positions export (.INI) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def ini(values, outfile, **kwargs):
        broker = values[0] and 'TC'
        # file_date = values[1]         # Not sent by TIAA-CREF
        acct_num = values[2][-6:] + values[2][:8]
        trans_code = values[3] and 'by'
        # cancel = values[4]            # Not sent by TIAA-CREF
        symbol = values[5].lower()
        sec_code = values[6]
        trade_date = values[7][:4] + values[7][-2:]  # Convert MMDDYYYY to MMDDYY
        quantity = float(values[8])
        net_amount = float(values[9]) and 0.0

        # Other values
        sec_type_code = 'mf'
        source = 'xxxxxxx'
        broker_fee = other_fee = SEC_fee = 0.0
        tk_code = 'TFR'
        tkc_desc = 'TRANSFERRED'
        option_symbol = ''
        settle_date = trade_date
        order_action = ''

        # NOTE: {trans_code: 'by', source: 'xxxxxxx', net_amount: 0.0}
        # for Receipt of Securities transaction
        output = ('{acct_num:14}{trans_code:2} {trade_date:6} '
                  '{sec_type_code:2} {symbol:9} {net_amount:>15.02f} {source:7} '
                  '{quantity:>15.05f} {broker:7} {broker_fee:>9.02f} {tk_code:4} '
                  '{tkc_desc:21} {other_fee:>16.04f} {SEC_fee:>16.04f} '
                  '{option_symbol:30} {settle_date:6} {order_action:20}')

        return output.format(**locals())

    # .INI files are really just transactions, so append to .trn
    outfile = outfile[:-4] + '.trn'
    mode = 'a'

    return convert_csv(infile, outfile, ini, file, mode=mode)


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
            'trn': Conversion('[aA][dD]*.[tT][rR][nN]', convert_tiaa_cref_trn_file, 'ban'),
            'trd': Conversion('[aA][dD]*.[tT][rR][dD]', convert_tiaa_cref_trd_file, 'bcd'),
            'ini': Conversion('[aA][dD]*.[iI][nN][iI]', convert_tiaa_cref_ini_file, 'bai'),
        }
    }

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?',
                        help='folder where data files are stored and converted',
                        default=os.environ.get('TIAA_CREF_DD', os.getcwd()))
    parser.add_argument('-c', '--custodian', choices=['tiaacref'], default='tiaacref',
                        help='abbreviation for data file(s) provider')
    parser.add_argument('-f', '--filetype', action='append',
                        choices=['ini', 'pri', 'sec', 'trd', 'trn'],
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
