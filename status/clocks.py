#!/usr/bin/env python
'''
status.clocks

Helper methods to deal with clock conversions
'''

import time
import calendar

def epoch2ts(epoch):
    
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(epoch))
    
def ts2epoch(ts):
    
    return calendar.timegm(time.strptime(ts, '%Y-%m-%d %H:%M:%S'))

def erddap_epoch2ts(epoch):
    
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(epoch))
    
def erddap_ts2epoch(ts):
    
    return calendar.timegm(time.strptime(ts, '%Y-%m-%dT%H:%M:%SZ'))
