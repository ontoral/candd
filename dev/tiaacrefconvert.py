import os
import sys
import datetime
import glob

PC_DATE_FORMAT = '%m%d%y'
FILE_TYPES = ['sec', 'pri']

def convert_csv(infile, outfile, converter=None):
    '''General purpose .CSV file conversion engine.'''
    # Convert data
    print '{infile}  -->  {outfile}'.format(**locals())
    with file(infile, 'r') as src, file(outfile, 'w') as dst:
        for line in src:
            values = line.split(',')
            conv = converter(**locals()) if converter else src
            dst.write(conv)

def convert_fixed(infile, outfile, fields, converter=None):
    '''General purpose fixed-width file conversion engine.'''
    # Convert data
    print '{infile}  -->  {outfile}'.format(**locals())
    with file(infile, 'r') as src, file(outfile, 'w') as dst:
        for line in src:
            values = []
            for field in fields:
                values.append(line[:field])
                line = line[field:]
            conv = converter(**locals()) if converter else src
            dst.write(conv)

def get_fidelity_path_from_tiaa_cref(tc_path):
    '''Generates a Fidelity export file path from a TIAA-CREF file path.'''
    # Get date
    filename = os.path.basename(tc_path)
    date = get_date_from_tiaa_cref(filename)

    # Get output filename
    path = os.path.dirname(tc_path)
    ext = base[-3:].lower()
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
        sec_type = 'MF' # if values[1] == 'OT' else 'MF'
        desc = values[2][0:40]
        cusip = values[21]
        return '{sec_type}{symbol:9}{desc:40}{cusip:>9}  0.00\n'.format(**locals())
    convert_csv(infile, outfile, sec)

def convert_tiaa_cref_pri_file(infile):
    '''Convert Prices export file from TIAA-CREF to Fidelity format.'''
    outfile = get_fidelity_path_from_tiaa_cref(infile)
    def pri(values, outfile, **kwargs):
        symbol = values[0]
        price = float(values[3])
        pc_datestr = os.path.basename(outfile)[2:8]
        return '{symbol:58}{price:>15.07f}{pc_datestr}\n'.format(**locals())
    convert_csv(infile, outfile, pri)

conversions = {
    'TC': {
        'pri': ('ad*.pri', convert_tiaa_cref_pri_file),
        'sec': ('ad*.sec', convert_tiaa_cref_sec_file),
    }
}

if __name__ == '__main__':
    usage = '''usage:
    {0} --help
    {0} [-c custodian][-t filetype[,filetype...]] [PATH]'''.format(*sys.argv)
    if len(sys.argv) == 2:
        path = os.path.realpath('.')
    else:
        path = os.path.realpath(sys.argv[-1])

    if '--help' in sys.argv:
        print usage
        sys.exit(0)

    if '-c' in sys.argv:
        custodian = sys.argv[sys.argv.index('-c') + 1].upper()
        if not custodian in conversions:
            print 'Invalid custodian'
            sys.exit(1)
    else:
        custodian = 'TC'

    if '-t' in sys.argv:
        filetypes = [ext.lower() for ext in split(sys.argv[sys.argv.index('-t') + 1], ',')]
    else:
        filetypes = FILE_TYPES

    for filetype in filetypes:
        if filetype not in conversions[custodian]:
            print 'Invalid file type', filetype
            continue
        conversion = conversions[custodian][filetype]
        filenames = glob.glob(os.path.join(path, conversion[0]))
        for filename in filenames:
            conversion[1](filename)
