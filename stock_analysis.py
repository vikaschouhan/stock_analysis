#!/usr/bin/env python

import argparse
import datetime
import re
import pickle

import pandas as pd
import pandas.io.data
from   pandas import Series, DataFrame

import matplotlib.pyplot as plt
import matplotlib as mpl

#################################
# global variables
################################
ticker_trend        = 0          # 0 means no trend, 1 means upward trend, 2 means downward trend
ticker_trend_tostr  = {0 : "flat", 1 : "bullish", 2 : "bearish", 99 : "nota"}

mova_days_dict      = {"20_days" : 20, "40_days" : 40, "60_days" : 60, "100_days" : 100}
compr_ravg_tup      = (20, 100)

pmin                = 10
pmax                = 50
trade_min           = 500000     # minium trade volume to remove less liquid stocks
volume_check        = 0
price_check         = 0
starttime           = datetime.datetime(2014, 01, 01)
endtime             = datetime.datetime.now()                # end time is current time
plot_yes            = 0
verbose             = 0                                      # verbose mode
glb_data_struct     = {}                                     # initialized to empty value
pickle_file_passed  = 0

#############################################################
# stock frame api functions
#############################################################
def call_yahoo_ticker_fun(ticker, starttime, endtime):
    glb_data_struct[ticker] = pd.io.data.get_data_yahoo(ticker, starttime, endtime)
    return glb_data_struct[ticker]

#
def call_internal_ticker_fun(ticker, starttime, endtime):
    """Waring !!! starttime and endtime are provided for api compatibility only. They\
            are not used by the underlying function."""
    return glb_data_struct[ticker]

call_ticker_fun = call_yahoo_ticker_fun


##############################################################
# Main loop. Iterate through each scripts and collect data
##############################################################
def main_loop(ticker_dict):
    assert(type(ticker_dict) == dict)

    for ticker in ticker_dict.keys():
        ## get_data_yahoo throws IOError exception is the ticker synmbol is not correct.
        ## catch it.
        try:
            stock_data       = call_ticker_fun(ticker, starttime, endtime)
        except IOError:
            if verbose:
                print "yahoo doesn't identify the ticker symbol {}" . format(ticker)
            continue
        except KeyError:
            if verbose:
                print "KeyError received on ticker symbol {}" . format(ticker)
            continue

        ## Calculate closing prices and volume data
        stock_close_data     = stock_data["Close"]
        stock_volume_data    = stock_data["Volume"]

        ## Check for average trade volumes for previous 100 days
        if volume_check and pd.rolling_mean(stock_volume_data, 100)[-1] < trade_min:
            if verbose:
                print "100 day median trade volume for {} is below {}" . format(ticker, trade_min)
            continue

        ## Check for price range
        if price_check and ((stock_close_data[-1] < pmin) or (stock_close_data[-1] > pmax)):
            if verbose:
                print "{} has latest closing price {}, hence is not in the defined price range" . format(ticker, stock_close_data[-1])
            continue

        ## Process the data
        process_stock_graph_series(stock_data, ticker_dict[ticker])

    # if plotting is enabled now is the time to display the graphs
    if plot_yes:
        plt.show()

##########################################################################
# Process and plot the stock movement along with some moving averages
##########################################################################
def process_stock_graph_series(obj, label):
    assert(type(obj) == pd.core.frame.DataFrame)

    mov_avg_h         = {};
    local_trend       = 99;
    close_data        = obj["Close"]
    vol_data          = obj["Volume"]
    adj_close_data    = obj["Adj Close"]

    # Populate all rolling means in a hash
    for dindex in mova_days_dict.keys():
        rolling_mean = pd.rolling_mean(adj_close_data, mova_days_dict[dindex])
        mov_avg_h[mova_days_dict[dindex]] = rolling_mean

    # Calculate local trend based on global parameters specified
    if mov_avg_h[max(compr_ravg_tup)][-1] < mov_avg_h[min(compr_ravg_tup)][-1]:
        local_trend = 1
    elif mov_avg_h[max(compr_ravg_tup)][-1] > mov_avg_h[min(compr_ravg_tup)][-1]:
        local_trend = 2
    else:
        local_trend = 99

    # Do a trend check
    # If the speicifed trend doesn't match with that specified as control parameter
    # return
    if ticker_trend != 0:
        if ticker_trend == local_trend:
            print "-------- {} shows {} trend" . format(label, ticker_trend_tostr[local_trend])
        else:
            return;
    else:
        print "-------- {} shows {} trend" . format(label, ticker_trend_tostr[local_trend])
    
    # plotting not allowed
    if not plot_yes:
        return;

    title = "Closing Price trend [with ";

    # Make subplots for showing various graphs in same fig
    #fig, axarr = plt.subplots(2, sharex=True)
    fig         = plt.figure(label)
    ax_cp       = plt.subplot2grid((4, 1), (0, 0), rowspan=2)
    ax_v        = plt.subplot2grid((4, 1), (2, 0), rowspan=1)
    ax_t        = plt.subplot2grid((4, 1), (3, 0), rowspan=1)

    # Plot closing price trend along with moving averages
    #
    ax_cp.plot(adj_close_data.index.tolist(), adj_close_data.tolist())
        
    for dindex in mova_days_dict.keys():
        rolling_mean = pd.rolling_mean(adj_close_data, mova_days_dict[dindex])
       
        x_list       = rolling_mean.index.tolist()
        y_list       = rolling_mean.tolist()
        title        = title + dindex + " "

        ax_cp.plot(x_list, y_list)

    title = title + " moving average]"
    ax_cp.grid()
    ax_cp.set_title(title)

    # Plot volume trend
    ax_v.bar(vol_data.index.tolist(), vol_data.tolist())
    ax_v.grid()
    ax_v.set_title("Volume trend")

    # Plot trend oscillator
    trend_data = detrended_price_oscillator(adj_close_data, 20)
    ax_t.plot(trend_data.index.tolist(), trend_data.tolist())
    ax_t.grid()
    ax_t.set_title("trend oscillator")


####################################################
# detrended_price_oscillator
####################################################
def detrended_price_oscillator(obj, N):
    assert(type(obj) == pandas.core.series.Series)
    obj_copy_local    = obj.copy()
    half_time         = int(N/2)

    for i in range(0, obj.size):
        obj_copy_local[i] = obj[i] - pd.rolling_mean(obj[0:i+1], half_time)[-1]

    return obj_copy_local

##############################################################
# std deviation (volatility index)
##############################################################
# Single pass volatility index calculator
def volatility_index_0(obj, N):
    assert(type(obj) == pandas.core.series.Series)
    step_1_list = pandas.rolling_std(obj, N).dropna()
    return pandas.rolling_std(step_1_list, step_1_list.size)[-1]

# Multipass volatility index calculator
def volatility_index_1(obj, N):
    assert(type(obj) == pandas.core.series.Series)
    n = N
    step_prev_list = obj
    while True:
        step_next_list = pandas.rolling_std(step_prev_list, n).dropna()
        #n = n * 2
        if step_next_list.size < n:
            return step_next_list[-1]
        step_prev_list = step_next_list


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

############################################
# main
############################################
if __name__ == '__main__':
    ticker_dict_n    = {}
    ticker_dict_t    = {}
    regex_m          = re.compile(r'([\w\.\-]+)[ \t\r\f\v]+"([ \w\W\t\r\f\v\-]+)"')       # match for valid line
    regex_h          = re.compile(r'(\w+)-\w+.NS')          # match for date format on command line
    regex_c          = re.compile(r'^#')                    # Match format for comment

    parser           = argparse.ArgumentParser()
    parser.add_argument("dfile", help="data description file generated by stock_list_pull script.", type=str)

    parser.add_argument("--vmin",     help="minimum volume limit",                      type=int)
    parser.add_argument("--pmin",     help="minimum price limit",                       type=int)
    parser.add_argument("--pmax",     help="maximum price limit",                       type=int)
    parser.add_argument("--tstart",   help="start time (day)",                          type=str)
    parser.add_argument("--tend",     help="end time (day)",                            type=str)
    parser.add_argument("--pfile",    help="pickle file",                               type=str)
    parser.add_argument("--trend",    help="ticker trend (0=all, 1=up, 2=down)",        type=int)
    parser.add_argument("--regex",    help="perl compatible regex for scrip search",    type=str)
    parser.add_argument("--plot",     help="plot graphs",                               action='store_true')
    parser.add_argument("--verbose",  help="verbose option",                            action='store_true')

    args             = parser.parse_args()

    # open description file
    f = open(args.dfile, "r");
    for line in f:
        # This means we encountered a comment
        if regex_c.match(line):
            continue

        res = regex_m.search(line)
        if res:
            ticker_dict_n[res.groups()[0]] = res.groups()[1]
        else:
            # This line is not recognised
            continue

    # check if pickle file was provided & redirect function pointer for
    # geting ticker values
    if args.pfile:
        glb_data_struct     = pickle.load(open(args.pfile, "rb"))
        call_ticker_fun     = call_internal_ticker_fun
        pickle_file_passed  = 1

    # Check price limits
    if args.pmin:
        pmin        = args.pmin
        price_check = 1
    if args.pmax:
        pmax        = args.pmax
        price_check = 1

    # check trade limit
    if args.vmin:
        trade_min    = args.vmin
        volume_check = 1

    # check time
    if args.tstart:
        starttime = convert_to_datetime_format(args.tstart)
    if args.tend:
        endtime   = convert_to_datetime_format(args.tend)

    # trend
    if args.trend:
        ticker_trend = args.trend

    # plot var
    if args.plot:
        plot_yes = 1

    # verbose
    if args.verbose:
        verbose = 1

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


    print "............... stock analysis parameters ...................."
    print "pandas version                                = {}" . format(pd.__version__)
    print "matplotlib version                            = {}" . format(mpl.__version__)
    print "configured ticker trend                       = {}" . format(ticker_trend_tostr[ticker_trend])
    print "configured moving averages                    = {}" . format(mova_days_dict.keys())
    print "configured moving averages for trend analysis = {}" . format(str((pmin, pmax)))
    print "configured duration start time                = {}" . format(starttime)
    print "configured duration end time                  = {}" . format(endtime)
    print "configured plotting allowed                   = {}" . format(plot_yes)
    print ".............................................................."
    print "\n"

    main_loop(ticker_dict_n)

    # Dump global data structure to pickle file
    if pickle_file_passed == 0:
        pickle.dump(glb_data_struct, open(args.dfile + ".pkl", "wb"))
