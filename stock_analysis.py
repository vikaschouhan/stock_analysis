#!/usr/bin/env python

import argparse
import datetime
import re

import pandas as pd
import pandas.io.data
from   pandas import Series, DataFrame

import matplotlib.pyplot as plt
import matplotlib as mpl

#################################
# global variables
################################
ticker_trend        = 0          # 0 means no trend, 1 means upward trend, 2 means downward trend
ticker_trend_tostr  = {0 : "flat", 1 : "bullish", 2 : "bearish"}

mova_days_dict      = {"10_days" : 10, "40_days" : 40, "60_days" : 60, "100_days" : 100}
compr_ravg_tup      = (10, 60)

pmin                = 10
pmax                = 50
trade_min           = 500000     # minium trade volume to remove less liquid stocks
volume_check        = 0
price_check         = 0
starttime           = datetime.datetime(2014, 01, 01)
endtime             = datetime.datetime.now()                # end time is current time
plot_yes            = 0
verbose             = 0                                      # verbose mode


##############################################################
# Main loop. Iterate through each scripts and collect data
##############################################################
def main_loop(ticker_dict):
    assert(type(ticker_dict) == dict)

    for ticker in ticker_dict.keys():
        ## get_data_yahoo throws IOError exception is the ticker synmbol is not correct.
        ## catch it.
        try:
            stock_data       = pd.io.data.get_data_yahoo(ticker, starttime, endtime)
        except IOError:
            if verbose:
                print "yahoo doesn't identify the ticker symbol {}" . format(ticker)
            continue

        ## Calculate closing prices and volume data
        stock_close_data     = stock_data["Close"]
        stock_volume_data    = stock_data["Volume"]

        ## Check for average trade volumes for previous 100 days
        if volume_check and pd.rolling_mean(stock_volume_data, 100)[-1] < trade_min:
            if verbose:
                print "100 day average trade volume for {} is below {}" . format(ticker, trade_min)
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
    ax_cp       = plt.subplot2grid((3, 1), (0, 0), rowspan=2)
    ax_v        = plt.subplot2grid((3, 1), (2, 0), rowspan=1)

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

    #fig.canvas.mpl_connect('button_press_event', on_click)

###################################################
# Not my code. Found somewhere on the internet
##################################################
def on_click(event):
    """Enlarge or restore the selected axis."""
    ax = event.inaxes
    if ax is None:
        # Occurs when a region not in an axis is clicked...
        return
    if event.button is 1:
        # On left click, zoom the selected axes
        ax._orig_position = ax.get_position()
        ax.set_position([0.1, 0.1, 0.85, 0.85])
        for axis in event.canvas.figure.axes:
            # Hide all the other axes...
            if axis is not ax:
                axis.set_visible(False)
    elif event.button is 3:
        # On right click, restore the axes
        try:
            ax.set_position(ax._orig_position)
            for axis in event.canvas.figure.axes:
                axis.set_visible(True)
        except AttributeError:
            # If we haven't zoomed, ignore...
            pass
    else:
        # No need to re-draw the canvas if it's not a left or right click
        return
    event.canvas.draw()


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
    regex_m          = re.compile(r'([\w\.\-]+)[ \t\r\f\v]+"([ \w\.\t\r\f\v\-]+)"')       # match for valid line
    regex_h          = re.compile(r'(\w+)-\w+.NS')          # match for date format on command line
    regex_c          = re.compile(r'^#')                    # Match format for comment

    parser           = argparse.ArgumentParser()
    parser.add_argument("dfile", help="data description file generated by stock_list_pull script.", type=str)

    parser.add_argument("--vmin",     help="minimum volume limit",                      type=int)
    parser.add_argument("--pmin",     help="minimum price limit",                       type=int)
    parser.add_argument("--pmax",     help="maximum price limit",                       type=int)
    parser.add_argument("--tstart",   help="start time (day)",                          type=str)
    parser.add_argument("--tend",     help="end time (day)",                            type=str)
    parser.add_argument("--trend",    help="ticker trend (0=all, 1=up, 2=down)",        type=int)
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

    # Check price limits
    if args.pmin:
        pmin        = args.pmin
        price_check = 1
    if args.pmax:
        pmax        = args.pmax
        price_check = 1

    # check trade limit
    if args.vmin:
        trade_min = args.vmin

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

    main_loop(ticker_dict_t)
