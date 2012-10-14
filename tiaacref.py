import os
import glob

EXPORT_DIR = '..\\tiaacref-exports\\'
conversions = {'pri': '..\\supplemental-prices\\',
               'sec': '..\\supplemental-securities\\',
               }

def get_fidelity_name(tc_name):
    base, ext = tc_name.lower().split('.')
    year = base[2:4]
    month = base[4:6]
    day = base[6:]
    return 'fi{month}{day}{year}.{ext}'.format(**locals())

def convert_line(line, filetype):
    return line

def tiaacref_to_fidelity(infile, outfile, filetype):
##    print 'infile ', infile
##    print 'outfile', outfile
    with file(infile, 'r') as src, file(outfile, 'w') as dst:
        for line in src:
            dst.write(convert_line(line, filetype))
    
    return False

def main():
    os.chdir(EXPORT_DIR)

    for filetype, path in conversions.iteritems():
        exports = glob.glob('*.'+filetype)
        for export in exports:
            infile = os.path.join(os.getcwd(), export)
            outfile = os.path.join(path, get_fidelity_name(export))
            outfile = os.path.realpath(outfile)
            if tiaacref_to_fidelity(infile, outfile, filetype):
##                print 'Backup to:', infile+'.bak'
                os.rename(infile, infile+'.bak')
##            else:
##                print 'No backup:', bakfile

if __name__ == '__main__':
    main()
