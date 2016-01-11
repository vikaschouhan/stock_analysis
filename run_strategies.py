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
#######################################################################

import argparse
import datetime
import re
import pickle
import sys

import pandas as pd
import pandas.io.data
from   pandas import Series, DataFrame

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
        ewma_s     = pandas.ewma(close_data, self.ma_short)
        ewma_l     = pandas.ewma(close_data, self.ma_long)
        if ewma_s[-1] > ewma_l[-1]:
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
        ewma_c     = pandas.ewma(close_data, 8)
        ewma_o     = pandas.ewma(open_data,  8)
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
        ewma_c     = pandas.ewma(close_data, 8)
        ewma_o     = pandas.ewma(open_data,  8)
        ewma_vol   = pandas.rolling_mean(volume,  50)
        ewma_50    = pandas.ewma(close_data, 50)
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
        ewma_c     = pandas.ewma(close_data, 8)
        ewma_o     = pandas.ewma(open_data,  8)
        ewma_vol   = pandas.rolling_mean(volume,  50)
        ewma_50    = pandas.ewma(close_data, 50)
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

############################################
# main
############################################
if __name__ == '__main__':
    params_dict      = {}
    ticker_dict_n    = {}
    ticker_dict_t    = {}
    regex_m          = re.compile(r'([\w\.\-]+)[ \t\r\f\v]+"([ \w\W\t\r\f\v\-]+)"')       # match for valid line
    regex_h          = re.compile(r'(\w+)-\w+.NS')          # match for date format on command line
    regex_c          = re.compile(r'^#')                    # Match format for comment

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


    print "###################################################################################"
    print "pandas version                                = {}".format(pd.__version__)
    print "vmin                                          = {}".format(params_dict["vmin"])
    print "date_start                                    = {}".format(params_dict["date_start"])
    print "date_end                                      = {}".format(params_dict["date_end"])
    print "###################################################################################"


    # define strategy
    strategy_this = ma_strategy2_8ema_crossover(3)

    for index in ticker_dict_n:
        try:
            data_this   = stock_data(scrip_id=index, date_start=params_dict["date_start"])
            vol_status  = params_dict["vmin"] <= pandas.ewma(data_this.get_volume(), 8)[-1]  # vmin <= average volume for some days
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
