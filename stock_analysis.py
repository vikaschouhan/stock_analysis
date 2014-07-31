#!/usr/bin/env python

import datetime

import pandas as pd
import pandas.io.data
from pandas import Series, DataFrame

print "pandas version = {}" . format(pd.__version__)

import matplotlib.pyplot as plt
import matplotlib as mpl

print "matplotlib version = {}" . format(mpl.__version__)

# Main loop. Iterate through each scripts and collect data
def main_loop(ticker_dict):
    assert(type(ticker_dict) == dict)

    starttime      = datetime.datetime(2011, 01, 1)         # start time
    endtime        = datetime.datetime.now()                # end time is current time
    
    for ticker in ticker_dict.keys():
        stock_data       = pd.io.data.get_data_yahoo(ticker, starttime, endtime)
        stock_close_data = stock_data["Close"]

        plot_stock_graph_series(stock_close_data, ticker_dict[ticker])

    plt.show()


# Plot the stock movement along with some moving averages
def plot_stock_graph_series(obj, label=""):
    assert(type(obj) == pd.core.series.Series)

    days_dict = {"10_days" : 10, "40_days" : 40, "60_days" : 60, "100_days" : 100}

    title = " [with ";
    plt.figure()
    plt.plot(obj.index.tolist(), obj.tolist(), label=label)
        
    for dindex in days_dict.keys():
        rolling_mean = pd.rolling_mean(obj, days_dict[dindex])
        x_list       = rolling_mean.index.tolist()
        y_list       = rolling_mean.tolist()
        title        = title + dindex + " "

        plt.plot(x_list, y_list, label=dindex)

    title = title + " moving average]"
    plt.grid()
    plt.title(label + title)

if __name__ == '__main__':
    ticker_dict    = {
                         "PCJEWELLER.BO"  :  "PC Jewellers Ltd",
                         "SOUTHINDBA.BO"  :  "South Indian Bank Ltd",
                         "GAEL.BO"        :  "Gujarat Ambuja Exports Ltd",
                         #"ARVINDREM.BO"   :  "Arvind Remedies",
                         "VINYL.BO"       :  "Vinyl Chemicals (India) Ltd",
                         "MIRZA.BO"       :  "Mirza International Ltd",
                     };
    main_loop(ticker_dict)
