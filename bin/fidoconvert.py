#!/usr/bin/env python

import os
import datetime
import glob
import argparse
import csv
from subprocess import call

PC_DATE_FORMAT = '%m%d%y'


def convert_csv(infile, outfile, converter, file=None, mode='w', headers=0):
    '''General purpose .CSV file conversion engine.'''
    # Convert data
    print '{infile}  -->  {outfile}'.format(**locals())
    with file or open(infile, 'r') as src:
        output = []
        unconverted = []
        csv_reader = csv.reader(src)
        for values in csv_reader:
            #print '1', headers, values
            if headers or not values[0]:
                headers -= 1
                continue

            #print 'past'
            converted = converter(**locals())
            if len(converted) == 0:
                if len(values[0]):
                    unconverted.append(values)
            else:
                output.append(converted)
                
    if len(output):
        with open(outfile, mode) as dst:
            dst.write('\r\n'.join(output))
        call(['chown', 'Administrators', outfile])
    if len(unconverted):
        print '\tunconverted rows in {infile}.err'.format(**locals())
        with open(infile + '.err', 'w') as errors:
            csv_writer = csv.writer(errors)
            csv_writer.writerows(unconverted)
        call(['chown', 'Administrators', infile + '.err'])

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
        symbol = 'tiaatrad-' if values[0].lower() == 'tiaatrad' else values[0].lower()
        sec_type = 'mf'
        desc = values[2][0:40]
        cusip = values[21]
        output = '{sec_type}{symbol:9}{desc:40}{cusip:>9}  0.00'

        return output.format(**locals())

    return convert_csv(infile, outfile, sec, file)


def convert_tiaa_cref_pri_file(infile, file=None):
    '''Convert Prices export (.PRI) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def pri(values, outfile, **kwargs):
        symbol = 'tiaatrad-' if values[0].lower() == 'tiaatrad' else values[0].lower()
        price = float(values[3])
        pc_datestr = os.path.basename(outfile)[2:8]
        output = '{symbol:58}{price:>15.07f}{pc_datestr}'

        return output.format(**locals())

    return convert_csv(infile, outfile, pri, file)


def convert_tiaa_cref_pos_file(infile, file=None):
    '''Convert Reconciliation export (.POS) from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)

    def pos(values, outfile, **kwargs):
        acct_num = values[0][-6:] + values[0][:8]
        sec_type = '' #values[2] and 'mf'  # Mutual Funds only from TIAA-CREF
        symbol = 'tiaatrad-' if values[3].lower() == 'tiaatrad' else values[3].lower()
        quantity = float(values[4])
        amount = float(values[5])

        # Other values
        acct_type = 1  # Cash account
        cusip = ''
        trade_date_quantity = settle_date_quantity = quantity
        close_price = ''  # >15.05f
        description = ''
        dts = os.path.basename(outfile)[2:8]
        date_str = '20{}{}'.format(dts[-2:], dts[:-2])  # Convert MMDDYY to YYYYMMDD
        factor = face_amount = clean_price = factored = ''
        option_symbol = ''
        rep1 = '000'  # Apparently C&D-specific values
        rep2 = 'J62'  # Apparently C&D-specific values

        # NOTE: Verify the need for closing_price, cusip, and description
        output = ('{acct_num:14} {acct_type:1d} {cusip:9} {symbol:9} '
                  '{trade_date_quantity:>15.05f} {settle_date_quantity:>15.05f} '
                  '{close_price:15} {description:40} {date_str:8} '
                  '{factor:17} {face_amount:18} {clean_price:18} {factored:1} '
                  '{sec_type:2} {option_symbol:30} {rep1:3}{rep2:3}')

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
                      'SECBUY': 'dv',
                      'DEP': 'dp',
                      'DIV': 'dv',
                      'INT': 'in',
                      'SELL': 'sl',
                      'WITH': 'wd',
                      'MFEE': 'wd'}.get(values[3], '')
        if trans_code == '':
            return ''
        symbol = 'tiaatrad-' if values[5].lower() == 'tiaatrad' else values[5].lower()
        if values[3] == 'INT':
            source = 'tiaatra'
        #elif values[3] == 'SECBUY':
            #source = values[5].lower()[:7]
        elif values[3] in ['WITH', 'MFEE']:
            source = 'client'
            symbol = 'cash'
        elif values[3] in ['DEP']:
            source = 'cash'
            symbol = 'cash'
        elif values[3] in ['BUY', 'SELL']:
            source = 'cash'
        else:
            source = 'client'
        cancel = values[4]
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
        sec_type_code = '' #'mf'
        tk_code, tkc_desc = {'by': ('BOT', 'BOUGHT'),
                             'dp': ('REC', 'RECEIVED FROM YOU'),
                             'dv': ('DIV', 'DIVIDEND'),
                             'in': ('INT', 'INTEREST'),
                             'sl': ('SLD', 'SOLD'),
                             'wd': ('DEL', 'DELIVERED TO YOU')}[trans_code]
        if values[3] == 'MFEE':
            tk_code, tkc_desc = 'ADF', 'ADVISOR FEE'
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
        symbol = 'tiaatrad-' if values[5].lower() == 'tiaatrad' else values[5].lower()
        sec_code = values[6]
        trade_date = values[7][:4] + values[7][-2:]  # Convert MMDDYYYY to MMDDYY
        quantity = float(values[8])
        net_amount = float(values[9]) and 0.0

        # Other values
        sec_type_code = '' #'mf'
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


def convert_schwab_pos_file(infile, file=None):
    '''Convert Positions export (.CSV) from Schwab to Fidelity format.'''
    stamp = infile.split('_')[-1]
    stamp = stamp.split('.')[0]
    with open(infile) as csv:
        acct_num = csv.readline().split()[4]
    acct_num = acct_num.replace('XXXX', os.path.basename(infile)[:4])
    outfile = 'fi' + acct_num + '_' + stamp + '.pos'

    def pos(values, outfile, acct_num=acct_num, **kwargs):
        symbol = values[0]
        description = values[1][:40]
        quantity = float(values[2])
        # values[3] == price
        # values[4] == price change $
        # values[5] == price change %
        # values[6] == market value
        # values[7] == day change $
        # values[8] == day change %
        # values[9] == Cost Basis
        # values[10] == Gain/Loss $
        # values[11] == Gain/Loss %
        # values[12] == Reinvest Dividends?
        # values[13] == Capital Gains?
        # values[14] == % Of Account
        # values[15] == Security Type
#"SPY","S P D R S&P 500 ETF TR EXPIRES 01/22/2118","117","$204.50","-$0.48","-0.23%","$23,926.50","-$56.16","-0.23%","$17,508.94","$6,417.56","+36.65%","No","--","62.16%","ETFs & Closed End Funds",
#"BUFBX","BUFFALO FLEXIBLE INCOME FUND","961.733","$14.32","-$0.02","-0.14%","$13,772.02","-$19.23","-0.14%","$12,600.00","$1,172.02","+9.3%","No","No","35.78%","Mutual Fund",
#"Cash & Money Market","--","--","--","--","--","$796.11","$0.00","0%","--","--","--","--","--","2.07%","Cash and Money Market",
#"Account Total","--","--","--","--","--","$38,494.63","-$75.39","-0.2%","$30,108.94","$7,589.58","+25.21%","--","--","--","--",
        sec_type = '' #values[2] and 'mf'  # Mutual Funds only from TIAA-CREF
        symbol = values[3].lower()
        quantity = float(values[4])
        amount = float(values[5])

        # Other values
        acct_type = 1  # Cash account
        cusip = ''
        trade_date_quantity = settle_date_quantity = quantity
        close_price = ''  # >15.05f
        dts = os.path.basename(outfile)[2:8]
        date_str = '20{}{}'.format(dts[-2:], dts[:-2])  # Convert MMDDYY to YYYYMMDD
        factor = face_amount = clean_price = factored = ''
        option_symbol = ''
        rep1 = '000'  # Apparently C&D-specific values
        rep2 = 'J62'  # Apparently C&D-specific values

        # NOTE: Verify the need for closing_price, cusip, and description
        output = ('{acct_num:14} {acct_type:1d} {cusip:9} {symbol:9} '
                  '{trade_date_quantity:>15.05f} {settle_date_quantity:>15.05f} '
                  '{close_price:15} {description:40} {date_str:8} '
                  '{factor:17} {face_amount:18} {clean_price:18} {factored:1} '
                  '{sec_type:2} {option_symbol:30} {rep1:3}{rep2:3}')

        return output.format(**locals())

    return convert_csv(infile, outfile, pos, file, mode='a', headers=3)


def convert_schwab_trn_file(infile, file=None):
    '''Convert Transactions export (.CSV) from Schwab to Fidelity format.'''
#    with open(infile) as csv:
#        acct_num = csv.readline().split()[4]
#    acct_num = acct_num.replace('XXXX', os.path.basename(infile)[:4])
    outfile = 'fi' + os.path.basename(infile)[2:12]

    def trn(values, outfile, **kwargs):
        #print values
        settle_date = values[0][:2] + values[0][3:5] + values[0][8:10]
        if len(values[0]) < 20:
            trade_date = settle_date
        else:
            trade_date = values[0][17:19] + values[0][20:22] + values[0][25:27]
        table = {'Buy': ('by', 'BOT', 'BOUGHT', 'cash'),
                 'Reinvest Shares': ('by', 'RIN', 'REINVESTMENT', 'cash'),
                 'Sell': ('sl', 'SLD', 'SOLD', 'cash'),
                 'CD Deposit Adj': ('cd', 'RDM', 'REDEEMED', 'cash'),
                 'CD Deposit Funds': ('skip', '', '', ''),
                 'Security Transfer': ('st', 'TFR', 'TRANSFERRED', 'cash'),
                 'Principal Payment': ('rc', 'PRN', 'PRINCIPAL PAYMENT', 'cash'),
                 'Bond Interest': ('in', 'INT', 'INTEREST', 'cash'),
                 'Bank Interest': ('in', 'INT', 'INTEREST', 'cash'),
                 'CD Interest': ('in', 'INT', 'INTEREST', 'cash'),
                 'Tax Withholding': ('pn', 'PN', 'TAX W/H', 'cash'),
                 'Stock Split': ('by', 'DST', 'DISTRIBUTION', 'cash'),
                 'Advisor Fee': ('wd', 'ADF', 'ADVISOR FEE', 'client'),
                 'Funds Paid': ('wd', 'DEL', 'DELIVERED TO YOU', 'client'),
                 'Auto S1 Debit': ('wd', 'DEL', 'DELIVERED TO YOU', 'client'),
                 'Visa Purchase': ('wd', 'DEL', 'DELIVERED TO YOU', 'client'),
                 'ATM Withdrawal': ('wd', 'DEL', 'DELIVERED TO YOU', 'client'),
                 'Funds Received': ('dp', 'REC', 'RECEIVED FROM YOU', 'client'),
                 'Auto S1 Credit': ('dp', 'REC', 'RECEIVED FROM YOU', 'client'),
                 'Schwab ATM Rebate': ('dp', 'REC', 'RECEIVED FROM YOU', 'client'),
                 'Pr Yr Cash Div': ('dv', 'DIV', 'DIVIDEND', 'cash'),
                 'Qualified Dividend': ('dv', 'DIV', 'DIVIDEND', 'cash'),
                 'Reinvest Dividend': ('rdv', 'DIV', 'DIVIDEND', 'dvwash'),
                 'Reinvest Shares': ('rby', 'RIN', 'REINVESTMENT', 'dvsplit'),
                 'Cash Dividend': ('dv', 'DIV', 'DIVIDEND', 'cash')}
        trans_code, tk_code, tkc_desc, source = table.get(values[1].strip(), ('', '', '', ''))
        if trans_code == '':
            return ''
        if trans_code == 'skip':
            values[0] = ''
            return ''
        symbol = values[2].lower().strip()
        # values[3] == security description
        quantity = abs(float(values[4].strip() or '0'))
        # values[5] == price
        # price = float(values[5].replace('$', '') or '0')
        broker_fee = float(values[6].replace('$', '').replace('*', '') or '0')
        net_amount = abs(float(values[7].replace('$', '').strip() 
                               or values[4]
                               or '0'))
        acct_num = values[9].strip()

        # Other values
        broker = 'SCHW'
        sec_type_code = ''
        # source = 'client' if trans_code in ['dp', 'wd'] else 'cash'

        # Non-trivial transactions
        if trans_code == 'pn':
            prefix = 'FED' if values[3][:3] == 'FED' else 'STATE'
            tk_code = prefix[0] + tk_code
            tkc_desc = prefix + ' ' + tkc_desc
            trans_code = 'wd'
            symbol = 'cash'
            source = 'xxxxxxx'
        elif trans_code in ['wd', 'dp']:
            sec_type_code = 'ca'
            tkc_desc = values[3][:21]
        elif trans_code == 'st':
            if symbol == 'no number':
                symbol = 'cash'
                if values[7].strip()[:1] == '-':
                    trans_code = 'wd'
                else:
                    trans_code = 'dp'
                source = 'xxxxxxx'
            else:
                trans_code = 'sl'
                net_amount = 0
        elif trans_code == 'rdv':
            trans_code = 'dv'
            quantity = 1
            broker = ''
        elif trans_code == 'rby':
            trans_code = 'by'
        elif trans_code == 'cd':
            trans_code = 'sl'
            net_amount = quantity

        other_fee = 0.0
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


def convert_fidelity_hist_file(infile, file=None):
    '''Convert History export (.CSV) from Fidelity to Fidelity format.'''
    # infile name: AccountHistoryForXXX-XXXXXX
    # outfile = infile[:-3] + 'trn'
    outfile = 'converted.trn'
    acct_num = infile.split('AccountHistoryFor')[1][:10]

    def trn(values, outfile, acct_num=acct_num, **kwargs):
        # values[0] == entry date
        months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                  'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                  'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
        trade_date = months[values[1][3:6]] + values[1][:2] + values[1][9:11]
        settle_date = months[values[2][3:6]] + values[2][:2] + values[2][9:11]
        trans_code = {'Buy': 'by',
                      'Sell': 'sl',
                      'Withdrawal': 'wd',
                      'Deposit': 'dp',
                      'Fee': 'dp',
                      'Interest': 'in',
                      'Dividend': 'dv',}.get(values[3].strip(), '')
        if trans_code == '':
            return ''
        # values[4] == transaction description
        symbol = values[5].lower().strip().split(' ')[0].replace('--', '')
        # values[6] == security description
        quantity = abs(float(values[7].strip().replace(',', '') or '0'))
        # values[8] == foreign quantity
        # values[9] == price
        # values[10] == currency
        # values[11] == foreign price
        # values[12] == currency
        net_amount = abs(float(values[13].replace('$', '').replace(',', '') or '0'))
        # values[14] == currency
        # values[15] == foreign net amount
        # values[16] == currency
        # values[17] == account type
        values[18] = '0' if values[18] == '--' else values[18].replace('$', '').replace(',', '')
        broker_fee = abs(float(values[18]))
        # values[19] == currency
        # values[20] == foreign commission
        # values[21] == currency
        tk_code = values[22]

        # Other values
        tkc_desc = {'BOT': 'BOUGHT',
                    'BUY': 'BOUGHT',
                    'SLD': 'SOLD',
                    'SEL': 'SOLD',
                    'JNL': 'JOURNAL',
                    'ADF': 'ADVISOR FEE',
                    'INT': 'INTEREST',
                    'DST': 'DISTRIBUTION',
                    'RDM': 'REDEEMED',
                    'PDP': 'NORMAL DISTR PARTIAL',
                    'ETT': 'MONEY LINE PAID EFT',
                    'FPN': 'FED TAX W/H',
                    'SPN': 'STATE TAX W/H',
                    'RIN': 'REINVESTMENT',
                    'DIV': 'DIVIDEND',}[tk_code]
        broker = ''
        sec_type_code = ''
        source = 'client' if trans_code in ['dp', 'wd'] else 'cash'
        other_fee = 0.0
        SEC_fee = 0.0
        option_symbol = ''
        order_action = ''
        output = ('{acct_num:14}{trans_code:2} {trade_date:6} '
                  '{sec_type_code:2} {symbol:9} {net_amount:>15.02f} {source:7} '
                  '{quantity:>15.05f} {broker:7} {broker_fee:>9.02f} {tk_code:4} '
                  '{tkc_desc:21} {other_fee:>16.04f} {SEC_fee:>16.04f} '
                  '{option_symbol:30} {settle_date:6} {order_action:20}')

        return output.format(**locals())

    return convert_csv(infile, outfile, trn, file, mode='a', headers=5)


def convert_plandestination_file(infile, file=None):
    '''Convert PlanDestination Transaction export (.CSV) to Fidelity format.'''
    # infile name: download_03042015.csv
    # outfile1 = fi030415.trn
    # outfile2 = fi030415.pos
    date = infile.split('_')[-1].split('.')[0]
    filename = 'fi' + date[:4] + date[6:]
    outfile1 = filename + '.trn'
    outfile2 = filename + '.pos'
    acct_num = '000000000'

    def trn(values, outfile=outfile1, acct_num=acct_num, **kwargs):
        trade_date = '{0:0>2}{1:0>2}{2[2]}{2[3]}'.format(*values[0].split('/'))
        #settle_date = trade_date
        trans_code = 'by' if values[1] == 'BUY' else 'sl'
        # values[2] == source
        symbol = values[3].lower()
        # values[4] == cusip
        # values[6] == investment (security description)
        quantity =  float(values[7])
        # values[8] == price
        net_amount = abs(float(values[9][1:]))
        # values[10] == activity
        {'ASSET ALLOCATION': 'BOT|SLD',
         'Corporate Fund Merger Adj': '',
         'EMPLOYEE PRE-TAX CONTRIBUTION': '',
         'EMPLOYER MATCHING CONTRIBUTION': '',
         'INCOME ADJUSTMENT': '',
         'PURCHASE DUE TO FUND SWAP': '',
         'PURCHASE DUE TO FUND TRANSFER': '',
         'REINVESTED DIVIDEND': 'DIV->RIN',
         'SALE DUE TO FUND SWAP': '',
         'SALE DUE TO FUND TRANSFER': '',
         'TRANSFER TO PERMANENT INVESTMENT': 'REC',}

        #if trans_code == '':
            #return ''

        # Other values
        sec_type_code = ''
        source = 'client' if trans_code in ['dp', 'wd'] else 'cash'
        broker = ''
        tk_code = values[22]
        tkc_desc = {'BOT': 'BOUGHT',
                    'BUY': 'BOUGHT',
                    'SLD': 'SOLD',
                    'SEL': 'SOLD',
                    'JNL': 'JOURNAL',
                    'ADF': 'ADVISOR FEE',
                    'INT': 'INTEREST',
                    'DST': 'DISTRIBUTION',
                    'RDM': 'REDEEMED',
                    'PDP': 'NORMAL DISTR PARTIAL',
                    'ETT': 'MONEY LINE PAID EFT',
                    'FPN': 'FED TAX W/H',
                    'SPN': 'STATE TAX W/H',
                    'RIN': 'REINVESTMENT',
                    'DIV': 'DIVIDEND',}[tk_code]
        other_fee = 0.0
        SEC_fee = 0.0
        option_symbol = ''
        order_action = ''
        output = ('{acct_num:14}{trans_code:2} {trade_date:6} '
                  '{sec_type_code:2} {symbol:9} {net_amount:>15.02f} {source:7} '
                  '{quantity:>15.05f} {broker:7} {broker_fee:>9.02f} {tk_code:4} '
                  '{tkc_desc:21} {other_fee:>16.04f} {SEC_fee:>16.04f} '
                  '{option_symbol:30} {settle_date:6} {order_action:20}')

        return output.format(**locals())

    return convert_csv(infile, outfile, trn, file, mode='a', headers=5)


def main():
    '''convert downloaded data files to Fidelity format'''

    # Small class to collect conversion details
    class Conversion(object):
        def __init__(self, glob_pattern, converter, backup_extension):
            self.glob_pattern = glob_pattern
            self.converter = converter
            self.backup_extension = backup_extension

        def convert_path(self, path, skip_backup=False):
            glob_pattern = os.path.join(path, self.glob_pattern)
            print 'Matching ' + glob_pattern
            filenames = glob.iglob(glob_pattern)
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
            'ini': Conversion('[aA][dD]*.[iI][nN][iI]', convert_tiaa_cref_ini_file, 'bai'),
            'pos': Conversion('[aA][dD]*.[pP][oO][sS]', convert_tiaa_cref_pos_file, 'bas'),
            'pri': Conversion('[aA][dD]*.[pP][rR][iI]', convert_tiaa_cref_pri_file, 'bap'),
            'sec': Conversion('[aA][dD]*.[sS][eE][cC]', convert_tiaa_cref_sec_file, 'bac'),
            'trd': Conversion('[aA][dD]*.[tT][rR][dD]', convert_tiaa_cref_trd_file, 'bcd'),
            'trn': Conversion('[aA][dD]*.[tT][rR][nN]', convert_tiaa_cref_trn_file, 'bak'),
        },
        'schwab': {
            'pos': Conversion('*pos.CSV', convert_schwab_pos_file, 'bsv'),
            'trn': Conversion('*trn.CSV', convert_schwab_trn_file, 'bsv'),
        },
        'fidelity': {
            'hist': Conversion('AccountHistoryFor*.csv', convert_fidelity_hist_file, 'bak'),
        },
    }

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?',
                        help='folder where data files are stored and converted',
                        default=os.environ.get('TIAA_CREF_DD', os.getcwd()))
    parser.add_argument('-c', '--custodian', choices=custodians.keys(),
                        default='tiaacref',
                        help='abbreviation for data file(s) provider')
    parser.add_argument('-f', '--filetype', action='append',
                        choices=['ini', 'pos', 'pri', 'sec', 'trd', 'trn'],
                        help='the extension of a filetype to convert')
    parser.add_argument('-s', '--skip-backup', action='store_true',
                        help='original files are not renamed after conversion')
    parser.add_argument('-d', '--history-download', nargs=1, type=file,
                        help='convert a history file downloaded from Fidelity')
    args = parser.parse_args()

    # Convert a history .csv from Fidelity website export
    if args.history_download:
        print args.history_download
        print args
#history.convert_file(args.history_download[0])
        return

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
