#!/usr/bin/env python

import os
import sys
import telnetlib

HOST = 'dd.trackdata.com'
STD_USER = 'usr.ddx.005'
STD_PASS = 'sesame'
USERCODE = os.environ.get('DDX_USERCODE', 'MX0505 HAPPY ON')

tn = telnetlib.Telnet(HOST)
ack = tn.read_until(' ****')
print ack
tn.write('\n')
tn.read_until('Username: ')
tn.write(STD_USER + '\n')
tn.read_until('Password: ')
tn.write(STD_PASS + '\n')
recent = tn.read_until(' -').split('\n')[2]
print recent
tn.write(USERCODE + '\n')
login = tn.read_some()
if login == 'INVALID USERCODE':
    print 'Login failed:', login
else:
    print 'Download some data!!'


#tn.write(user + "\n")
#if password:
#    tn.read_until("Password: ")
#    tn.write(password + "\n")

#tn.write("ls\n")
#tn.write("exit\n")

#print tn.read_all()

