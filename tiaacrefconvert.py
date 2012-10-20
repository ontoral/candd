import os
import datetime
import glob

def convert_file(infile, converter):
    # Get date components
    base = os.path.basename(infile)
    yr = int(base[2:4]) + 2000
    mo = int(base[4:6])
    dy = int(base[6:8])
    dt = datetime.date(yr, mo, dy)

    # Get output filename
    path = os.path.dirname(infile)
    ext = base[8:]
    pc_date = dt.strftime('%m%d%y')
    outfile = os.path.join(path, 'fi{pc_date}{ext}'.format(**locals()))

    # Convert data
    print '{infile}  -->  {outfile}'.format(**locals())
    with file(infile, 'r') as src, file(outfile, 'w') as dst:
        for sec in src:
            values = sec.split(',')
            conv = converter(**locals())
            dst.write(conv)

def convert_sec(infile):
    def sec(values, **kwargs):
        symbol = values[0]
        sec_type = 'MF' # if values[1] == 'OT' else 'MF'
        desc = values[2][0:40]
        cusip = values[21]
        return '{sec_type}{symbol:9}{desc:40}{cusip:>9}  0.00\n'.format(**locals())
    convert_file(infile, sec)

def convert_pri(infile):
    def pri(values, pc_date, **kwargs):
        symbol = values[0]
        price = float(values[3])
        return '{symbol:58}{price:>15.07f}{pc_date}\n'.format(**locals())
    convert_file(infile, pri)


if __name__ == '__main__':
    files = glob.glob(os.path.join('..', 'data', 'ad*.sec'))
    for filename in files:
        convert_sec(filename)

    files = glob.glob(os.path.join('..', 'data', 'ad*.pri'))
    for filename in files:
        convert_pri(filename)

