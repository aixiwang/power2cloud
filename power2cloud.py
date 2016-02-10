#---------------------------------------------------------------------------
# meter2cloud
# -- a python tool to read meter data from jsy_mk_135 module
#
# BSD 3-clause license is applied to this code
# Copyright(c) 2015 by Aixi Wang <aixi.wang@hotmail.com>
#---------------------------------------------------------------------------
# fix issues:
# * convert_bin_to_current exception (2015-4-20)
#---------------------------------------------------------------------------

import serial
import thread
import time
import os
import sys


global status
global jpg_bin
global serial_s
global resp_bin

sys.path.append('../')
from pyiotlib import *

serial_s = None
status = 0
resp_bin = ''
#------------------------------------------
# common utils routines
#------------------------------------------
def readfile(filename):
    f = file(filename,'rb')
    fs = f.read()
    f.close()
    return fs

def writefile(filename,content):
    f = file(filename,'wb')
    fs = f.write(content)
    f.close()
    return
    
def has_file(filename):
    if os.path.exists(filename):
        return True
    else:
        return False
        
def remove_file(filename):
    if has_file(filename):
        os.remove(filename)
    
#----------------------
# ser_task
#----------------------
def ser_task():
    global status
    global resp_bin
    global serial_s
    print 'ser_task thread starting...'

    SERIAL_DEV_PATH = 'COM2'       
    try:
        SERIAL_DEV_PATH = sys.argv[1]
    except:
        pass
       
    print 'serial port:',SERIAL_DEV_PATH
    
    while True:
        if serial_s == None:
            while True:
                try:
                    serial_s = serial.Serial(SERIAL_DEV_PATH, 4800, timeout=0,parity='N',stopbits=1,xonxoff=0,rtscts=0)
                    break;
                except:
                    print 'waiting to reconnect serial port ...'                
                    time.sleep(5)

        status = 0
        resp_bin = ''
        while True:
            try:
                c1 = serial_s.read(1024)
                
                if len(c1) == 37 and c1[0:3] == '\x01\x03\x20':
                    print '>'
                    #print c1.encode('hex')
                    
                    resp_bin = c1
                    status = 2
                    return
                    
                else:
                    print '='                
                    #print c1
                    time.sleep(1)

            except:
                print 'exception...1'
                serial_s = None
                time.sleep(1)
                return
                
#----------------------
# start_ser_thread
#----------------------            
def start_ser_thread():
    thread.start_new_thread(ser_task,())

def start_read_jsy_mk_135(serial_s):
    print 'start_read_jsy_mk_135'
    try:
        if serial_s != None:
            serial_s.write('\x01\x03\x00\x48\x00\x08\xc4\x1a')
            return 0
    except:
        print 'exception: serial port is not ready'
        return -1
        
#----------------------
# convert_bin_to_current
#---------------------- 
def convert_bin_to_current(s):
    #print s.encode('hex')
    try:
        d = ord(s[7])*256*256*256 + ord(s[8])*256*256 + ord(s[9])*256 + ord(s[10])
        return 0,d
    except:
        return -1,0
#----------------------
# show_help
#----------------------   
def show_help():
    print '\r\n------------------------------------------------------------------'
    print 'Usage:'
    print '    python meter2cloud.py [serial_path_name] '
    print '------------------------------------------------------------------'

    
#----------------------
# main
#----------------------
if __name__ == "__main__":
    serial_s = None
    show_help()
    
    while (1):
        try:
            start_ser_thread()
            while(serial_s == None):
                print '\r\nserial port is not ready'
                time.sleep(1)
            
            if start_read_jsy_mk_135(serial_s) < 0:
                time.sleep(1)
                continue
                
            i = 3;
            while(status != 2 and i > 0):
                print 'status:',status
                i -= 1
                time.sleep(1)
            
            if i == 0:
                time.sleep(10)
                print 'timeout, sleep 10 sec, try again'
                continue
                
            print 'data is ready to get meter data'

            retcode,d = convert_bin_to_current(resp_bin)
            if retcode < 0:
                time.sleep(5)
                continue

            f1 = float(d)/10000
            print 'current=',f1
            auth_key = readfile('./key.txt')
            rpc = app_sdk(auth_key,server_ip='115.29.178.81',server_port=7777)
            #rpc = app_sdk(auth_key,server_ip='192.168.2.241',server_port=7777)    
            try:
                json_out = rpc.save_data('P-000001',str(f1))
                print json_out
                if (json_out['code'] == 0):
                    print 'upload data ok'
                else:
                    print 'upload fail'           
                time.sleep(10)
            except:
                print 'upload data exception!'
                time.sleep(60)
        except:
            print 'top level exception'
            time.sleep(60)
        

    
