BATCH_FILE = 'batch-status-report-2012.txt'

price = 0.0
unpriced = False
price_date = ''
price_file = None
with file(BATCH_FILE, 'r') as batch:
    for line in batch:
        line = line.strip()
        if line.startswith('-----'):
            unpriced = True
            continue
        if not unpriced:
            continue
        if unpriced and not line:
            break

        # Handle unpriced securities here
        dated = line[0:8]
        sec_type = line[12:27].strip()
        symbol = line[27:46].strip()

        if dated != price_date:
            price_date = dated
            if price_file:
               price_file.close() 
               price_file = None

            if not price_file:
                pf_name = 'fi'+''.join(dated.split('/'))+'.pri'
                price_file = file(pf_name, 'w')
                print pf_name
                
        price_file.write('{symbol:58}{price:>15.07f}\n'.format(**locals()))
        print '\t'+symbol
    price_file and price_file.close()

