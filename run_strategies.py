#!/usr/bin/env python

#######################################################################
# Author         : Vikas Chouhan
# email          : presentisgood@gmail.com
# latest updated : 11th January 2016
# license        : GPLv2
#
#
# Download stock data from yahoo financial website and run
# custom strategies over all the scrips to screen for the stocks
# satisfying our criteria.
# Update : 15th Jan 2016
#          Added multiprocessing support. Since this script is I/O
#          heavy, using large number of processes can substantially
#          bring down total execution time.
#######################################################################

import argparse
import datetime
import re
import pickle
import sys
import multiprocessing
from   multiprocessing import Process
from   itertools import islice

import pandas as pd
import pandas.io.data
from   pandas import Series, DataFrame

####################################################
# support functions
####################################################
# splice a dictionary into chunks each of size 'size'
def dict_chunks(dict_data, size):
    it = iter(dict_data)
    for i in xrange(0, len(dict_data), size):
        yield {k:dict_data[k] for k in islice(it, size)}

####################################################
# convert to datetime format
####################################################
def convert_to_datetime_format(date_str):
    regex_date_format1 = re.compile(r'(\d+):(\d+):(\d+)')
    regex_date_format2 = re.compile(r'(\d+)-(\d+)-(\d+)')

    if regex_date_format1.match(date_str):
        res = regex_date_format1.match(date_str)
    elif regex_date_format2.match(date_str):
        res = regex_date_format2.match(date_str)
    else:
        raise Exception("date format wrong.")
    return datetime.datetime(int(res.groups()[0]), int(res.groups()[1]), int(res.groups()[2]))

#################################################
# stock_data
#################################################
class stock_data(object):
    def __str__(self):
        return "stock_data"

    def __init__(self, scrip_id, date_start, date_end="Now", name=''):
        assert(type(date_start) == str and type(date_end) == str and type(scrip_id) == str and type(name) == str)
        # Convert date_end to datetime format
        if date_end == "Now":
            date_end         = datetime.datetime.now()
        else:
            date_end         = convert_to_datetime_format(date_end)

        self.scripid         = scrip_id
        self.name            = ''
        self.date_start      = convert_to_datetime_format(date_start)
        self.date_end        = date_end
        if self.name == '':
            self.name        = self.scripid
        # Get data from yahoo.
        self.load_from_yahoo()

    def load_from_yahoo(self):
        """Load stock information from yahoo."""
        self.data            = pandas.io.data.get_data_yahoo(self.scripid, self.date_start, self.date_end)
        self.__adj_close_s   = self.data["Adj Close"]
        self.__close_s       = self.data["Close"]
        self.__open_s        = self.data["Open"]
        self.__volume_s      = self.data["Volume"]
        self.__high_s        = self.data["High"]
        self.__low_s         = self.data["Low"]

    ## Getters
    def get_close(self):
        return self.__close_s.copy()
    def get_adj_close(self):
        return self.__adj_close_s.copy()
    def get_open(self):
        return self.__open_s.copy()
    def get_high(self):
        return self.__high_s.copy()
    def get_low(self):
        return self.__low_s.copy()
    def get_volume(self):
        return self.__volume_s.copy()

############################################
# Implement custom stretegies
############################################
class ma_strategy0(object):
    def __init__(self, ma_short, ma_long):
        self.ma_short = ma_short
        self.ma_long  = ma_long
    # enddef

    def __call__(self, stk_data):
        close_data = stk_data.get_adj_close()
        ewma_s     = pandas.ewma(close_data, span=self.ma_short)
        ewma_l     = pandas.ewma(close_data, span=self.ma_long)
        if ewma_s[-1] > ewma_l[-1]:
            return True
        return False

# Moving average crossover strategy
class ma_strategy0_ema_crossover(object):
    def __init__(self, speriod, lperiod, days_diff=2, days_delay=0):
        self.speriod    = speriod                                               # Short ema period
        self.lperiod    = lperiod                                               # Long ema period
        self.days_diff  = days_diff
        self.days_delay = days_delay
        self.off_start  = -1 - self.days_delay                                  # start offset
        self.off_end    = -1 - self.days_delay - self.days_diff                 # end offset (< start offset)
        self.off_curr   = self.off_start                                        # current offset
        self.dslopepos  = 1                                                     # n_days for taking +ve slope
        self.dslopeneg  = 4                                                     # n_days for taking -ve slope
        self.dvol       = 50                                                    # n_days for taking volume moving median
    # enddef

    def __call__(self, stk_data):
        close_data = stk_data.get_close()
        open_data  = stk_data.get_open()
        volume     = stk_data.get_volume()
        ewma_s     = pandas.ewma(close_data, span=self.speriod)
        ewma_l     = pandas.ewma(close_data, span=self.lperiod)
        # Check for 8ema crossover of open and close prices as well as
        # a sudden spurt in volume
        rt_cross   = ewma_s[self.off_curr] > ewma_l[self.off_curr]              # Current short ema > long ema
        lt_cross   = ewma_s[self.off_end] <= ewma_l[self.off_end]               # short ema < long ema days_dff before
        tr_rev     = (ewma_s[self.off_curr] > ewma_l[self.off_curr-1]) and \
                     (ewma_s[self.off_end] <= ewma_l[self.off_end-4])           # Trend reversal
        # Check status
        if rt_cross and lt_cross:
            return True
        return False



class ma_strategy_8ema_crossover(object):
    def __init__(self, days_diff=2):
        self.days_diff  = days_diff
    # enddef

    def __call__(self, stk_data):
        close_data = stk_data.get_close()
        open_data  = stk_data.get_open()
        volume     = stk_data.get_volume()
        ewma_c     = pandas.ewma(close_data, span=8)
        ewma_o     = pandas.ewma(open_data,  span=8)
        ewma_vol   = pandas.rolling_mean(volume,  50)
        # Check for 8ema crossover of open and close prices as well as
        # a sudden spurt in volume
        if ewma_c[-1] > ewma_o[-1] and \
           ewma_c[-1-self.days_diff] <= ewma_o[-1-self.days_diff] and \
           volume[-1] > 3 * ewma_vol[-1]:
            return True
        return False

# Along with two 8 ema crossovers, also look for a sudden spurt in volume from average.
#
class ma_strategy2_8ema_crossover(object):
    def __init__(self, days_diff=2):
        self.days_diff  = days_diff
    # enddef

    def __call__(self, stk_data):
        close_data = stk_data.get_close()
        open_data  = stk_data.get_open()
        volume     = stk_data.get_volume()
        ewma_c     = pandas.ewma(close_data, span=8)
        ewma_o     = pandas.ewma(open_data,  span=8)
        ewma_vol   = pandas.rolling_mean(volume,  50)
        ewma_50    = pandas.ewma(close_data, span=50)
        # Check for 8ema crossover of open and close prices as well as
        # a sudden spurt in volume
        rt_cross   = ewma_c[-1] > ewma_o[-1]    # Current 8ema[close] > 8ema[open]
        lt_cross   = ewma_c[-1-self.days_diff] <= ewma_o[-1-self.days_diff]  # 8ema[close] < 8ema[open] days_dff before
        vol_status = volume[-1] > 3 * ewma_vol[-1] # Current volume > 3 times average volume
        ema50_tr   = ewma_50[-1] > 0   # Long term trend in bullish

        # Check status
        if rt_cross and lt_cross and vol_status and ema50_tr:
            return True
        return False

# Along with two 8 ema crossovers, also look for a sudden spurt in volume from average.
# Also check for -ve slope to +ve slope reversal for 8ema
class ma_strategy3_8ema_crossover(object):
    def __init__(self, days_diff=2):
        self.days_diff  = days_diff
    # enddef

    def __call__(self, stk_data):
        close_data = stk_data.get_close()
        open_data  = stk_data.get_open()
        volume     = stk_data.get_volume()
        ewma_c     = pandas.ewma(close_data, span=8)
        ewma_o     = pandas.ewma(open_data,  span=8)
        ewma_vol   = pandas.rolling_mean(volume,  50)
        ewma_50    = pandas.ewma(close_data, span=50)
        # Check for 8ema crossover of open and close prices as well as
        # a sudden spurt in volume
        rt_cross   = ewma_c[-1] > ewma_o[-1]    # Current 8ema[close] > 8ema[open]
        lt_cross   = ewma_c[-1-self.days_diff] <= ewma_o[-1-self.days_diff]  # 8ema[close] < 8ema[open] days_dff before
        vol_status = volume[-1] > 3 * ewma_vol[-1] # Current volume > 3 times average volume
        ema50_tr   = ewma_50[-1] > 0   # Long term trend in bullish
        tr_rev     = (ewma_c[-1] > ewma_c[-2]) and (ewma_c[-1-self.days_diff] <= ewma_c[-1-self.days_diff-4])

        # Check status
        if rt_cross and lt_cross and vol_status and tr_rev:
            return True
        return False

class ma_strategy4_8ema_crossover(object):
    def __init__(self, days_diff=2, days_delay=0):
        self.days_diff  = days_diff
        self.days_delay = days_delay
        self.off_start  = -1 - self.days_delay                                  # start offset
        self.off_end    = -1 - self.days_delay - self.days_diff                 # end offset (< start offset)
        self.off_curr   = self.off_start                                        # current offset
        self.dslopepos  = 1                                                     # n_days for taking +ve slope
        self.dslopeneg  = 4                                                     # n_days for taking -ve slope
        self.dvol       = 50                                                    # n_days for taking volume moving median
    # enddef

    def __call__(self, stk_data):
        close_data = stk_data.get_close()
        open_data  = stk_data.get_open()
        volume     = stk_data.get_volume()
        ewma_c     = pandas.ewma(close_data, span=8)
        ewma_o     = pandas.ewma(open_data,  span=8)
        med_vol    = pandas.rolling_mean(volume,  self.dvol)
        ewma_50    = pandas.ewma(close_data, span=50)
        # Check for 8ema crossover of open and close prices as well as
        # a sudden spurt in volume
        rt_cross   = ewma_c[self.off_curr] > ewma_o[self.off_curr]              # Current 8ema[close] > 8ema[open]
        lt_cross   = ewma_c[self.off_end] <= ewma_o[self.off_end]               # 8ema[close] < 8ema[open] days_dff before
        vol_thr    = 3 * med_vol[self.off_curr]                                 # Volume threshold
        vol_status = volume[self.off_curr] > vol_thr or \
                     volume[self.off_curr-1] > vol_thr or \
                     volume[self.off_curr-2] > vol_thr                          # if any of last three days vol > volume threshold
        ema50_tr   = ewma_50[self.off_curr] > 0                                 # Long term trend in bullish
        tr_rev     = (ewma_c[self.off_curr] > ewma_c[self.off_curr-1]) and \
                     (ewma_c[self.off_end] <= ewma_c[self.off_end-4])

        # Check status
        if rt_cross and lt_cross and vol_status and tr_rev:
            return True
        return False

############################################
# main and helpers
############################################

# Execute strategy pipeline.
# Multiple strategies can be executed one by one
# Even multiple strategies can be combined in OR fashion
#
# TODO:
# strategy_pipeline (either tuple of tuples, list of tuples, tuple of lists, list of lists)
# (
#        ( strategy00, strategy01, strategy02, ....),
#        ( strategy10, strategy11, strategy12, ....), 
#        ( .... )
# )
def main_thread(ticker_dict):
    for index in ticker_dict:
        try:
            data_this   = stock_data(scrip_id=index, date_start=params_dict["date_start"])
            #vol_status  = params_dict["vmin"] <= pandas.ewma(data_this.get_volume(), 8)[-1]  # vmin <= average volume for some days
            vol_status  = True
            # Check if volume requirement is satisfied and then only apply our strategy
            if vol_status:
                status  = strategy_this(data_this)
                if status:
                    print "scripid = {}, company_name = {}".format(index, ticker_dict_n[index])
                # endif
            # endif
        except:
            #print "Couldn't load data for {}".format(index)
            pass
    # endfor
# enddef

if __name__ == '__main__':
    params_dict      = {}
    ticker_dict_n    = {}
    ticker_dict_t    = {}
    regex_m          = re.compile(r'([\w\.\-]+)[ \t\r\f\v]+"([ \w\W\t\r\f\v\-]+)"')       # match for valid line
    regex_h          = re.compile(r'(\w+)-\w+.NS')          # match for date format on command line
    regex_c          = re.compile(r'^#')                    # Match format for comment
    #cpu_count        = multiprocessing.cpu_count()          # Get cpu count for launching 4 processes simultaneously
    process_count    = 20                                   # Set process count

    parser           = argparse.ArgumentParser()
    parser.add_argument("dfile", help="data description file generated by stock_list_pull script.", type=str)
    parser.add_argument("--vmin",     help="minimum volume limit",                      type=int)
    parser.add_argument("--tstart",   help="start time (day)",                          type=str)
    parser.add_argument("--tend",     help="end time (day)",                            type=str)
    parser.add_argument("--regex",    help="perl compatible regex for scrip search",    type=str)
    parser.add_argument("--verbose",  help="verbose option",                            action='store_true')

    args             = parser.parse_args()

    # open description file
    f = open(args.dfile, "r");
    for line in f:
        # This means we encountered a comment
        if regex_c.match(line):
            continue

        # Old way
        #
        #res = regex_m.search(line)
        #if res:
        #    ticker_dict_n[res.groups()[0]] = res.groups()[1]
        #else:
        #    # This line is not recognised
        #    continue
        #
        # New way
        # Updated on 11th Jan, 2016
        res = line.split(',')
        ticker_dict_n[res[0]] = res[1]
    # endfor

    # check trade limit
    if args.vmin:
        params_dict["vmin"] = args.vmin
    else:
        params_dict["vmin"] = 1
    # endif

    # check time
    if args.tstart:
        params_dict["date_start"] = args.tstart
    else:
        params_dict["date_start"] = "2014:01:01"
    # endif
    if args.tend:
        params_dict["date_end"]   = args.tend
    else:
        params_dict["date_end"]   = "Now"
    # endif

    # verbose
    if args.verbose:
        params_dict["verbose"]    = True
    else:
        params_dict["verbose"]    = False
    # endif

    ##########
    # hack required for script names with -EQ.NS subscript (for eg. PCJEWELLERS-EQ.NS).
    # They don't work with pandas yahoo api at this time.
    # Hackish solution is to derive the corresponding BSE name, which doesn't contain -EQ
    # substring.
    for index in ticker_dict_n.keys():
        name_new  = index
        res       = regex_h.search(index)
        if res:
            name_new = res.groups()[0] + ".BO"
        ticker_dict_t[name_new] = ticker_dict_n[index]

    # Clear the original list
    ticker_dict_n = {}

    # Check for the any passed regex
    if args.regex:
        regex_c      = re.compile('{}' . format(args.regex))
        for index in ticker_dict_t.keys():
            if regex_c.match(index) or regex_c.match(ticker_dict_t[index]):
                ticker_dict_n[index] = ticker_dict_t[index]
    else:
        ticker_dict_n = ticker_dict_t
    # endif

    # define strategy
    strategy_this = ma_strategy4_8ema_crossover(days_diff=5, days_delay=8)
    chunk_size    = len(ticker_dict_n)/process_count
    chunk_size    = chunk_size + 1 if (len(ticker_dict_n) % process_count) else chunk_size
    chunk_gen     = dict_chunks(ticker_dict_n, chunk_size)            # Get chunk generator

    print "###################################################################################"
    print "pandas version                                = {}".format(pd.__version__)
    print "vmin                                          = {}".format(params_dict["vmin"])
    print "date_start                                    = {}".format(params_dict["date_start"])
    print "date_end                                      = {}".format(params_dict["date_end"])
    print "todays_date                                   = {}".format(datetime.datetime.now())
    print "number of processes                           = {}".format(process_count)
    print "total entries per process                     = {}".format(chunk_size)
    print "total entries in database                     = {}".format(len(ticker_dict_n))
    print "strategy used                                 = {}".format(strategy_this.__class__.__name__)
    print "###################################################################################"

    # Launch separate threads
    for process_this in range(0, process_count):
        dict_this       = chunk_gen.next()
        process_this    = Process(target=main_thread, args=(dict_this,))
        process_this.start()
    # endfor
# enddef
