#!/usr/bin/python
# """"""""""""""""""""""""analysis.py"""""""""""""""""""""""""""""""""""
# This file contains classes which facilitate technical analysis of stocks
# for purpose of trading. Plotting facilities are based on matplotlib library.
# Stock analysis is based on pandas library.
#
# Author : Vikas Chouhan (presentisgood@gmail.com)
# Copyright 2014
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# It is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file; see the file COPYING. If not, write to the
# Free Software Foundation, 51 Franklin Street - Fifth Floor, Boston,
# MA 02110-1301, USA.

import datetime
import pickle
import re
import numpy

import pandas
import pandas.io.data
from   pandas import Series, DataFrame

import matplotlib
import matplotlib.pyplot

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

############################################################################
# wrapper over matplotlib's show()
def show():
    matplotlib.pyplot.show()

###############################################################################
# new plotting class library
###############################################################################
class plots_class:
    """Customized plotting class"""
    # Plot type constants
    PLOT_TYPE_BAR      = 0
    PLOT_TYPE_PLOT     = 1
    LEGEND_PROP        = {'loc' : "upper left", 'fontsize' : 6}

    def __str__(self):
        return "plots_class"

    def __init__(self, label=''):
        """
        Initialize a new figure object.
        @args
            label         = label to be assigned to figure.
        """
        self.fig       = matplotlib.pyplot.figure(label)
        self.data      = {}
        self.n_plots   = 0
        self.n_columns = 1
        self.n_rows    = 0
        self.h_ratios  = []

    def __del__(self):
        matplotlib.pylab.close(self.fig)
        self.data      = {}
        self.n_plots   = 0
        self.n_rows    = 0
        self.h_ratios  = []

    def __layout_subplots(self):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        plot_obj_l     = []
        x              = 0
        for i in range(0, self.n_plots):
            plot_obj_l.append(matplotlib.pyplot.subplot2grid((self.n_rows, 1), (x, 0), rowspan=self.h_ratios[i]))
            x = x + self.h_ratios[i]
        self.plot_obj  = plot_obj_l

    def __inc_plots(self):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        self.n_plots   = self.n_plots + 1

    def __dec_plots(self):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        self.n_plots   = self.n_plots - 1
     
    # FIXME:
    # This function is hack to ensure that self.data behaves as a list while popping an
    # element i.e it's keys readjust automatically depending on which frame was popped.
    # We may need to fix it later on.
    def __pop_plots_data(self, pop_key):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        n_data         = {}
        for i in range(0, pop_key):
            n_data[i]  = self.data[i]
        for i in range(pop_key, len(self.data.keys()) - 1):
            n_data[i]  = self.data[i+1]
        self.data      = n_data

    def __remove_frame(self, frame):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        self.fig.clf()
        self.__dec_plots()                           # Decrement number of n_plots
        self.h_ratios.remove(self.h_ratios[frame])   # Calculate new ratios
        self.n_rows    = sum(self.h_ratios)          # Calculate fresh number of rows
        self.__layout_subplots()                     # refresh previous layouts with new configuration
        self.__pop_plots_data(frame)
        
        # Draw all plots again
        for i in range(0, self.n_plots):
            for dict_this in self.data[i]:
                if dict_this["plot_type"] == self.PLOT_TYPE_PLOT:
                    self.__draw(i, dict_this["x_list"], dict_this["y_list"], dict_this["label"], self.PLOT_TYPE_PLOT)
                elif dict_this["plot_type"] == self.PLOT_TYPE_BAR:
                    self.__draw(i, dict_this["x_list"], dict_this["y_list"], dict_this["label"], self.PLOT_TYPE_BAR)
            self.plot_obj[i].legend(self.__get_labels_list_for_frame(i), loc=self.LEGEND_PROP['loc'])

    def __append_new(self, ratio=1):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        self.fig.clf()                           # Clear figure
        self.__inc_plots()                       # Increment number of n_plots
        self.h_ratios.append(ratio)              # Calculate new hratios
        self.n_rows    = sum(self.h_ratios)      # Calculate fresh number of rows
        self.__layout_subplots()                 # refresh previous layouts with new configuration

        # Draw previous n_plots again
        for i in range(0, (self.n_plots - 1)):
            for dict_this in self.data[i]:
                if dict_this["plot_type"] == self.PLOT_TYPE_PLOT:
                    self.__draw(i, dict_this["x_list"], dict_this["y_list"], dict_this["label"], self.PLOT_TYPE_PLOT)
                elif dict_this["plot_type"] == self.PLOT_TYPE_BAR:
                    self.__draw(i, dict_this["x_list"], dict_this["y_list"], dict_this["label"], self.PLOT_TYPE_BAR)
            self.plot_obj[i].legend(self.__get_labels_list_for_frame(i), loc=self.LEGEND_PROP['loc'])
    
    def __check_valid_frame(self, ratio, frame):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        if frame == None:
            self.__append_new(ratio)
            return self.n_plots - 1
        else:
            assert(frame < self.n_plots)
            return frame

    def __append_data(self, frame, data):
        """
        Internal function.
        WARNING !! Don't call this function.
        """ 
        if not (frame in self.data):
            self.data[frame] = []
        self.data[frame].append(data)

    def __get_frame_data(self, frame):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        assert(frame in self.data)
        return self.data[frame]

    def __get_labels_list_for_frame(self, frame):
        return map(lambda x: x["label"], self.__get_frame_data(frame))

    def __get_default_next_label(self, frame, label=''):
        if label == '' or label == None:
            if (frame in self.data):
                return "frame" + str(frame) + "_diag" + str(len(self.data[frame]))
            else:
                return "frame" + str(frame) + "_diag0"
        else:
            return label

    def __add_legend(self, frame):
        self.plot_obj[frame].legend(self.__get_labels_list_for_frame(frame), loc="upper left")


    def __plot(self, frame, x_list, y_list, label):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        obj             = self.plot_obj[frame]
        obj.plot(x_list, y_list, label=label)

    def __bar(self, frame, x_list, y_list, label):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        obj             = self.plot_obj[frame]
        obj.bar(x_list, y_list, label=label)

    def __draw(self, frame, x_list, y_list, label, plot_type):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        obj_this       = self.plot_obj[frame]
        obj_this.grid()
        label          = self.__get_default_next_label(frame, label)
        obj_this.set_title(label)
        if plot_type == self.PLOT_TYPE_PLOT:
            self.__plot(frame, x_list, y_list, label)
        elif plot_type == self.PLOT_TYPE_BAR:
            self.__bar(frame, x_list, y_list, label)
        self.fig.tight_layout()
        return label

    def del_frame(self, frameno):
        """
        Delete a frame.
        @args
            frameno       = frame number to be deleted.
        """
        self.__remove_frame(frameno)

    def set_frame_title(self, frameno, title):
        """
        Set frame's title explicitly.Useful when drawing several plots on same frame.
        @args
            title         = title
        """
        assert(frameno < len(self.plot_obj))
        self.plot_obj[frameno].set_title(title)
        return frameno

    def plot(self, x_list, y_list, label='', ratio=1, frame=None):
        """
        Plot the actual data.
        NOTE : Both x_list and y_list should be of same size.
        @args
            x_list        = list of x-axis values.
            y_list        = list of y-axis values.
            label         = label for this plot.
            ratio         = height ratio for this plot.
            frame         = frame number to be passed in case, this plot needs to be superimposed on an already
                            drawn plot.
        """
        frame_new      = self.__check_valid_frame(ratio, frame)
        label          = self.__draw(frame_new, x_list, y_list, label, self.PLOT_TYPE_PLOT)
        self.__append_data(frame_new,\
                  {"x_list" : x_list, "y_list" : y_list, "label" : label, "plot_type" : self.PLOT_TYPE_PLOT})
        self.__add_legend(frame_new)
        return frame_new
        

    def bar(self, x_list, y_list, label='', ratio=1, frame=None):
        """
        Plot the actual data as vertical bars.
        NOTE : Both x_list and y_list should be of same size.
        @args
            x_list        = list of x-axis values.
            y_list        = list of y-axis values.
            label         = label for this plot.
            ratio         = height ratio for this plot.
            frame         = frame number to be passed in case, this plot needs to be superimposed on an already
                            drawn plot.
        """
        frame_new      = self.__check_valid_frame(ratio, frame)
        label          = self.__draw(frame_new, x_list, y_list, label, self.PLOT_TYPE_BAR)
        self.__append_data(frame_new,\
                  {"x_list" : x_list, "y_list" : y_list, "label" : label, "plot_type" : self.PLOT_TYPE_BAR})
        self.__add_legend(frame_new)
        return frame_new

    def plot_pandas_series(self, series, label='', ratio=1, frame=None):
        """
        Plot pandas.core.series.Series type data.
        @args
            series        = data of type pandas.Series.series
            label         = label for this plot.
            ratio         = height ratio for this plot.
            frame         = frame number to be passed in case, this plot needs to be superimposed on an already
                            drawn plot.
        """
        assert(type(series) == pandas.core.series.Series)
        return self.plot(series.index.tolist(), series.tolist(), label, ratio, frame)

    def bar_pandas_series(self, series, label='', ratio=1, frame=None):
        """
        Plot pandas.core.series.Series type data as vertical bars.
        @args
            series        = data of type pandas.Series.series
            label         = label for this plot.
            ratio         = height ratio for this plot.
            frame         = frame number to be passed in case, this plot needs to be superimposed on an already
                            drawn plot.
        """
        assert(type(series) == pandas.core.series.Series)
        return self.bar(series.index.tolist(), series.tolist(), label, ratio, frame)



#################################################################
# parameters class
#################################################################
class parameters:
    """Parameters class."""
    #TICKER_TREND_TYPE_FLAT       = 0
    TICKER_TREND_TYPE_BULLISH    = 1
    TICKER_TREND_TYPE_BEARISH    = 2
    TICKER_TREND_TYPE_NOTA       = 99

    ticker_trend_tostr  = {
                                 #TICKER_TREND_TYPE_FLAT     : "flat",
                                 TICKER_TREND_TYPE_BULLISH  : "bullish",
                                 TICKER_TREND_TYPE_BEARISH  : "bearish",
                                 TICKER_TREND_TYPE_NOTA     : "nota"
                          }

    @classmethod
    def trend_tostr(cls, trend):
        assert(trend in cls.ticker_trend_tostr)
        return cls.ticker_trend_tostr[trend]

    def __str__(self):
        return "parameters"

    def __init__(self):
        self.ticker_trend        = self.TICKER_TREND_TYPE_BULLISH
        self.mova_days_dict      = {"20_days" : 20, "40_days" : 40, "60_days" : 60, "100_days" : 100}
        self.compr_ravg_tup      = (20, 100)
        
        self.pmin                = 10
        self.pmax                = 50
        self.trade_min           = 500000     # minium trade volume to remove less liquid stocks
        self.volume_check        = False
        self.price_check         = False
        self.date_start          = datetime.datetime(2014, 01, 01)
        self.date_end            = datetime.datetime.now()                # end time is current time
        self.plot_yes            = False
        self.verbose             = False                                  # verbose mode
        self.pickle_file_passed  = False
        self.pickle_file         = 'default'
        #self.db_file             = 'default.pkl'
        self.db_file             = 'default.txt'

    def print_info(self):
        print "..............parameters.............................................."
        print "ticker_trend       = {}" . format(self.trend_tostr(self.ticker_trend))
        print "mova_days_dict     = {}" . format(self.mova_days_dict)
        print "moving_av_tup      = {}" . format(self.compr_ravg_tup)
        print "pmin               = {}" . format(self.pmin)
        print "pmax               = {}" . format(self.pmax)
        print "trade_min          = {}" . format(self.trade_min)
        print "volume_check       = {}" . format(self.volume_check)
        print "price_check        = {}" . format(self.price_check)
        print "date_start         = {}" . format(self.date_start)
        print "date_end           = {}" . format(self.date_end)
        print "plot_yes           = {}" . format(self.plot_yes)
        print "verbose            = {}" . format(self.verbose)
        print "pickle_file_passed = {}" . format(self.pickle_file_passed)
        print "pickle_file        = {}" . format(self.pickle_file)
        print "db_file            = {}" . format(self.db_file)
        print "....................................................................."

    def add_mova_days(self, days, days_label):
        assert(type(days) == int and type(days_label) == str)
        self.mova_days_dict.update({days_label : days})

    def set_input_pickle_file(self, filename):
        self.pickle_file_passed = 1
        self.pickle_file        = filename

    def set_output_pickle_file(self, filename):
        self.pickle_file        = filename

    def set_input_database_file(self, filename):
        self.db_file            = filename

    def set_ticker_trend(self, trend):
        assert(trend in ticker_trend_tostr)
        self.ticker_trend       = trend

    def set_price_min(self, price):
        self.pmin               = price
        self.price_check        = True

    def set_price_max(self, price):
        self.pmax               = price
        self.price_check        = True

    def set_volume_min(self, vol):
        self.trade_min          = vol
        self.volume_check       = True

    def set_date_start(self, date):
        self.date_start         = convert_to_datetime_format(date)

    def set_date_end(self, date):
        self.date_end           = convert_to_datetime_format(date)

    def enable_plot(self):
        self.plot_yes           = True

    def enable_verbose(self):
        self.verbose            = True



#################################################################
# stock analysis class
#################################################################
class stock_analysis_class:
    """
    Analysis algorithms for stock indicators.

    Plotting features.
    =====================================================================================
    Almost all technical indicators returning list of data in some form, also have two
    optional function parameters called 'hratio' and 'frame'.
    These parameters only get active, when an instance of this class is initialized with
    plot=True parameter.
    hratio indicates the height ratio of this plot on the figure canvas.
    frame indicates that we want this plot to get superimposed on some previously drawn plot.
    frame numbers always start from zero. Each new plot gets consequetively next frame numbers,
    starting from zero.
    """
    use_pickle_dict          = False
    pickle_dict              = {}
    WEILDERS_CONSTANT        = 14

    def __str__(self):
        return "stock_analysis_class"

    def __init__(self, scripid, date_start, date_end="Now", name='', plot=False):
        """
        @Args
            scripid      = yahoo scrip id of the stock (for eg. SOUTHINDBA.BO for South India Bank.)
            date_start   = start date in form of string in \"YYYY:MM:DD\" or \"YYYY-MM-DD\" format.
            date_end     = don't specify for current date otherwise specify in similar manner to date_start.
            name         = name of the scrip (optional).
            plot         = start plotting features. If enabled, each technical analysis will start plotting it's
                           corresponding graphs.
        """
        assert(type(date_start) == str and type(date_end) == str and type(scripid) == str and type(name) == str)
        # Convert date_end to datetime format
        if date_end == "Now":
            date_end         = datetime.datetime.now()
        else:
            date_end         = convert_to_datetime_format(date_end)

        self.scripid         = scripid
        self.name            = ''
        self.date_start      = convert_to_datetime_format(date_start)
        self.date_end        = date_end
        self.plot            = False
        self.plot_obj        = None

        if self.name == '':
            self.name        = self.scripid
        if plot:
            self.plot        = True
            self.plot_obj    = plots_class(label=scripid)

        self.frame_price     = None
        self.frame_dmx       = None

        # Get data from yahoo if use_pickle_dict is not enabled
        if not self.use_pickle_dict:
            self.load_from_yahoo()
        else:
            self.load_from_internal_database()

    def __del__(self):
        self.scripid         = None
        self.name            = None
        self.date_start      = None
        self.date_end        = None
        if self.plot:
            self.plot        = False
            del self.plot_obj
        self.frame_price     = None
        self.frame_dmx       = None

    @classmethod
    def load_database_from_pickle(cls, filename):
        """
        This function initializes the internal database from a pickle file which was generated by this very module.
        This enables this class to pick stock data from the local database instead of yahoo server and hence enables
        very fast calculations to be done on the data.
        @args
            filename     = name of the pickle file.
        """
        cls.pickle_dict      = pickle.load(open(filename, "rb"))

    @classmethod
    def store_database_to_pickle(cls, filename):
        """
        This function dumps the internal database to a pickle file which can be used later on by this very same module.
        @args
            filename     = name of the pickle file.
        """
        pickle.dump(cls.pickle_dict, open(filename, "wb"))

    def __plot(self, series_this, ratio=1, frame=None, label=''):
        """
        Internal plot function.
        @args
            series_this  = and object of type pandas.Series.series ready to be plotted.
            ratio        = height ratio of the plot
            frame        = frame number of the plot. This is required when this plot needs to be superimposed
                           on a previous plot.
        """
        if self.plot:
            return self.plot_obj.plot_pandas_series(series_this, ratio=ratio, frame=frame, label=label)
        return None

    def __bar(self, series_this, ratio=1, frame=None, label=''):
        """
        Helper bar function.
        @args
            series_this  = and object of type pandas.Series.series ready to be plotted.
            ratio        = height ratio of the plot
            frame        = frame number of the plot. This is required when this plot needs to be superimposed
                           on a previous plot.
        """
        if self.plot:
            return self.plot_obj.bar_pandas_series(series_this, ratio=ratio, frame=frame, label=label)
        return None

    def __set_frame_title(self, frame, title):
        """
        Set frame's title explicitly.
        """
        return self.plot_obj.set_frame_title(frame, title)

    def __select_frame_price(self, frame=None):
        """
        Internal function.
        WARNING !! Don't call this function.
        """
        if frame == None:
            return self.frame_price
        else:
            return frame

    def delete_frame(self, frame):
        """
        Delete a previously drawn frame
        @args
            frame        = frame number of a previous plot which needs to be removed from the figure.
                           On deletion, rest of the plots readjust automatically on the figure canvas.
                           This only works if stock_analysis_class instance was instantiated with
                           plot=True option.
        """
        if self.plot:
            # Clear any previously assigned frame, if it matches the frame to be deleted.
            if self.frame_price == frame:
                self.frame_price = None
            elif self.frame_dmx == frame:
                self.frame_dmx = None
            # Delete the frame
            self.plot_obj.del_frame(frame)

    def load_from_yahoo(self):
        """Load stock information from yahoo."""
        self.stock_data      = pandas.io.data.get_data_yahoo(self.scripid, self.date_start, self.date_end)
        self.__adj_close_s   = self.stock_data["Adj Close"]
        self.__close_s       = self.stock_data["Close"]
        self.__open_s        = self.stock_data["Open"]
        self.__volume_s      = self.stock_data["Volume"]
        self.__high_s        = self.stock_data["High"]
        self.__low_s         = self.stock_data["Low"]

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

    def load_from_internal_database(self):
        """Load stock information from internal pickle database."""
        self.stock_data      = pickle_dict[self.scripid]

    def closing_price(self, hratio=1, frame=None):
        """
        Return and plot(if plot enabled) closing price trend.
        @args
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame.
        """
        clp                  = self.__adj_close_s
        self.frame_price     = self.__plot(clp, ratio=hratio, frame=self.__select_frame_price(frame), label="closing price")
        return clp

    def volume(self, hratio=1, frame=None):
        """
        Return and plot(if plot enabled) volume trend.
        @args
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame number.
        """
        vol                  = self.__volume_s
        self.__bar(vol, ratio=hratio, frame=frame, label="volume")
        return vol

    def moving_average(self, N, hratio=1, frame=None):
        """
        Return and plot(if plot enabled) Moving average for closing price trend.
        @args
            N            = time period in days used for moving average calculation.
            hratio       = height ratio of the plot.
            frame        = prespecified frame (optional)
        """
        label_this           = "ma_" + str(N)
        mva                  = pandas.rolling_mean(self.__adj_close_s.copy(), N)
        self.frame_price     = self.__plot(mva, ratio=hratio, frame=self.__select_frame_price(frame), label=label_this)
        return mva

    def exponential_moving_average(self, N, hratio=1, frame=None):
        """
        Return and plot(optional) Exponential moving average for closing prices.
        @args
            N            = time period in days used for moving average calculation.
            hratio       = height ratio of the plot.
            frame        = optional prespecified frame number.
        """
        label_this           = "ema_" + str(N)
        ema                  = pandas.ewma(self.__adj_close_s.copy(), N)
        self.frame_price     = self.__plot(ema, ratio=hratio, frame=self.__select_frame_price(frame), label=label_this)
        return ema

    def wilders_moving_average(self, hratio=1, frame=None):
        """
        Return and plot Wilder's moving average.
        @args
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame number.
        """
        N                    = 27
        wma                  = self.exponential_moving_average(N)
        # Don't plot again as it's already taken care by self.exponential_moving_average()
        #self.frame_price     = self.__plot(wma, ratio=hratio, frame=self.__select_frame_price(frame))
        return wma

    def multiple_moving_averages(self, hratio=1, frame=None):
        """
        Multiple moving averages.
        Right now uses 3, 5, 7, 10, 12, 15 for short term MA and
        30, 35, 40, 45, 50 and 60 as long term MA.
        @args
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame number.
        """
        close_copy_this      = self.__adj_close_s.copy()
        short_term_mva       = {}
        long_term_mva        = {}
        frame_this           = frame

        short_term_mva[3]    = pandas.rolling_mean(close_copy_this,    3)
        short_term_mva[5]    = pandas.rolling_mean(close_copy_this,    5)
        short_term_mva[7]    = pandas.rolling_mean(close_copy_this,    7)
        short_term_mva[10]   = pandas.rolling_mean(close_copy_this,   10)
        short_term_mva[12]   = pandas.rolling_mean(close_copy_this,   12)
        short_term_mva[15]   = pandas.rolling_mean(close_copy_this,   15)

        long_term_mva[30]    = pandas.rolling_mean(close_copy_this,   30)
        long_term_mva[35]    = pandas.rolling_mean(close_copy_this,   35)
        long_term_mva[40]    = pandas.rolling_mean(close_copy_this,   40)
        long_term_mva[45]    = pandas.rolling_mean(close_copy_this,   45)
        long_term_mva[50]    = pandas.rolling_mean(close_copy_this,   50)
        long_term_mva[60]    = pandas.rolling_mean(close_copy_this,   60)

        # Try plotting
        for i in short_term_mva:
            frame_this       = self.__plot(short_term_mva[i], ratio=hratio, frame=frame_this)
        for i in long_term_mva:
            frame_this       = self.__plot(long_term_mva[i], ratio=hratio, frame=frame_this)

        return { "ST_MA" : short_term_mva, "LT_MA" : long_term_mva }

    def moving_average_convergence_divergence(self, hratio=1, frame=None):
        """
        Moving average convergence divergence based on 26 day & 12 day ema's difference as
        MACD signal and using a 9 day ema of MACD as crossover signal.
        @args
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame no.
        """
        close_copy_this      = self.__adj_close_s.copy()
        frame_this           = frame

        long_term_ewma       = pandas.ewma(close_copy_this, 26)
        short_term_ewma      = pandas.ewma(close_copy_this, 12)
        conv_div_sig         = short_term_ewma -long_term_ewma
        inter_sig            = pandas.ewma(conv_div_sig, 9)

        # Try plotting
        frame_this           = self.__plot(conv_div_sig, ratio=hratio, frame=frame_this, label="26_12_ema_diff")
        frame_this           = self.__plot(inter_sig, ratio=hratio, frame=frame_this, label="9_ema_std")

        return { "STD_SIG" : inter_sig, "CONV_DIV_SIG" : conv_div_sig }

    def keltner_channels(self, N=None, hratio=1, frame=None):
        """
        Keltner channels/bands based on N day high and low averages.If not specified,
        N is taken as 10 days. It also plots closing price, hence no separate plotting is
        required for closing price.
        @args
            N            = Time period in days used for high and low moving averages (10 by default).
            hratio       = An optional height ratio of the plot.
            frame        = An optional prespecified frame no.
        """
        close_copy_this      = self.__adj_close_s.copy()
        high_copy_this       = self.__high_s.copy()
        low_copy_this        = self.__low_s.copy()
        frame_this           = frame
        if N == None:
            N                = 10

        high_limit_ind       = pandas.rolling_mean(high_copy_this, N)
        low_limit_ind        = pandas.rolling_mean(low_copy_this, N)

        # Try plotting
        frame_this           = self.__plot(high_limit_ind, ratio=hratio, frame=frame_this, label="high_ind")
        frame_this           = self.__plot(low_limit_ind, ratio=hratio, frame=frame_this, label="low_ind")
        frame_this           = self.__plot(close_copy_this, ratio=hratio, frame=frame_this, label="close_price")
        frame_this           = self.__set_frame_title(frame_this, "keltner_channels")

        return { "HIGH_SIG" : high_limit_ind, "LOW_SIG" : low_limit_ind }

    # Uses adjusted closing price
    def on_balance_volume(self, hratio=1, frame=None):
        """
        Return and plot On balance volume indicator.
        @args
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame no.
        """
        adj_close_l          = self.__adj_close_s.copy()
        obv_l                = self.__volume_s.copy()
        obv_prev             = obv_l[0]
        close_prev           = adj_close_l[0]
        for i in range(1, obv_l.size):
            if adj_close_l[i] > close_prev:
                obv_l[i]     = obv_prev + obv_l[i]
            elif adj_close_l[i] < close_prev:
                obv_l[i]     = obv_prev - obv_l[i]
            close_prev       = adj_close_l[i]
            obv_prev         = obv_l[i]
        self.__bar(obv_l, ratio=hratio, frame=frame, label="on balance volume")
        return obv_l

    def accumulation_distribution(self, hratio=1, frame=None):
        """
        Return and plot Accumulation Distribution Data
        @args
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame number
        """
        close_copy_this      = self.__close_s.copy()
        low_copy_this        = self.__low_s.copy()
        high_copy_this       = self.__high_s.copy()
        volume_copy_this     = self.__volume_s.copy()
        frame_this           = frame

        money_flow_vol       = (2*close_copy_this - low_copy_this - high_copy_this)/(high_copy_this - low_copy_this) * volume_copy_this
        accum_dist           = money_flow_vol.dropna().cumsum()

        frame_this           = self.__plot(accum_dist, ratio=hratio, frame=frame_this, label="accum_dist")

        return accum_dist

    def chaikin_money_flow(self, N=None, hratio=1, frame=None):
        """
        Return and plot Chaikin Money flow oscillator.
        @args
            N            = Number of days used for calculation (If not specified it's taken 20 by default).
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame number
        """
        close_copy_this      = self.__close_s.copy()
        open_copy_this       = self.__open_s.copy()
        low_copy_this        = self.__low_s.copy()
        high_copy_this       = self.__high_s.copy()
        volume_copy_this     = self.__volume_s.copy()
        CMF                  = close_copy_this.copy()
        list_size            = close_copy_this.size
        frame_this           = frame
        if N == None:
            N                = 20

        money_flow_mult      = ((close_copy_this - low_copy_this) - (high_copy_this - close_copy_this))/(high_copy_this - low_copy_this)

        # sanitize money_flow_mult in cases where high, low etc are all same
        # (for eg. on national holidays when the market is closed). This happpens due to erraneous
        # data reporting from yahoo, wherein it includes weekdays when stock exchange is closed.
        for i in range(list_size-1, 0, -1):
            # Replace all NaNs with 0
            if numpy.isnan(money_flow_mult[i]):
                money_flow_mult[i]  = 0

        # Money flow volume
        money_flow_vol       = money_flow_mult * volume_copy_this

        # 
        for i in range(list_size-1, N, -1):
            money_flow_vol_slice   = money_flow_vol[0:i+1]
            volume_slice           = volume_copy_this[0:i+1]
            CMF[i]                 = pandas.rolling_mean(money_flow_vol_slice, N)[-1]/pandas.rolling_mean(volume_slice, N)[-1]
        for i in range(N, -1, -1):
            CMF[i]                 = numpy.float64(numpy.nan)
        # Drop NaNs
        CMF                  = CMF.dropna()

        ## Plot it
        frame_this           = self.__plot(CMF, ratio=hratio, frame=frame_this, label="CMF")
        frame_this           = self.__set_frame_title(frame_this, "chaikin_money_flow")

        return CMF

    def directional_movement_system(self, N=None, hratio=1, frame=None):
        """
        Return and plot Directional movement system as developed by Dr. Welles Wilder.
        @args
            N            = time period in days. If not provided, default (14 days) will be assumed.
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame no
        @return
            list of +di, -di and adx
        """
        high_copy        = self.__high_s.copy()
        low_copy         = self.__low_s.copy()
        adj_close_copy   = self.__adj_close_s.copy()
        close_copy       = self.__close_s.copy()
        plus_dm          = self.__high_s.copy()
        minus_dm         = self.__low_s.copy()
        list_size        = plus_dm.size
        true_range       = minus_dm.copy()
        cmpr_line_25     = pandas.Series([25]*true_range.index.size, true_range.index.tolist())

        # Not sure which close to use.
        close_copy_this  = close_copy
        if N == None:
            N            = self.WEILDERS_CONSTANT

        for i in range(list_size-1, 0, -1):
            delta_high          = high_copy[i] - high_copy[i-1]
            delta_low           = low_copy[i-1] - low_copy[i]

            if (delta_high < 0 and delta_low < 0) or delta_high == delta_low:
                plus_dm[i]      = 0
                minus_dm[i]     = 0
            elif delta_high > delta_low:
                plus_dm[i]      = delta_high
                minus_dm[i]     = 0
            elif delta_high < delta_low:
                plus_dm[i]      = 0
                minus_dm[i]     = delta_low
            # Insider day
            #if plus_dm[i] > 0 and minus_dm[i] > 0:
            #    pass
            true_range[i]   = max(abs(high_copy[i] - low_copy[i]), abs(high_copy[i] - close_copy_this[i-1]), abs(close_copy_this[i-1] - low_copy[i]))

        plus_adm         = pandas.ewma(plus_dm,      N)
        minus_adm        = pandas.ewma(minus_dm,     N)
        atr              = pandas.ewma(true_range,   N)
        plus_di          = plus_adm/atr * 100
        minus_di         = minus_adm/atr * 100
        dx               = abs(plus_di - minus_di)/(plus_di + minus_di) * 100
        adx              = pandas.ewma(dx,           N)

        frame_this       = self.__plot(plus_di, ratio=hratio, frame=frame, label="+di")
        frame_this       = self.__plot(minus_di, frame=frame_this, label="-di")
        frame_this       = self.__plot(adx, frame=frame_this, label="adx")
        frame_this       = self.__set_frame_title(frame_this, "drectional movement system")
        #self.__plot(cmpr_line_25, frame=frame_this, label="hl_25")

        return [plus_di, minus_di, adx]

    def momentum_oscillator(self, N=None, hratio=1, frame=None):
        """
        Return and plot Momentum oscillator.
        @args
            N            = time period in days. If not provided, default (14 days) will be assumed.
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame number
        """
        adj_close_copy   = self.__adj_close_s.copy()
        close_copy       = self.__close_s.copy()
        momentum         = close_copy.copy()

        # Not sure which close to use.
        close_copy_this  = close_copy
        if N == None:
            N            = self.WEILDERS_CONSTANT

        for i in range(momentum.size-1, -1, -1):
            prev_i       = max(i-N, 0)
            momentum[i]  = close_copy_this[i]/close_copy_this[prev_i]

        frame            = self.__plot(momentum, ratio=hratio, frame=frame, label="momentum oscillator")
        frame            = self.__set_frame_title(frame, "momentum oscillator")

        return momentum

    def momentum(self, N=None, hratio=1, frame=None):
        """
        Return and plot Momentum oscillator.
        @args
            N            = time period in days. If not provided, default (14 days) will be assumed.
            hratio       = height ratio of the plot.
            frame        = An optional prespecified frame no.
        """
        adj_close_copy   = self.__adj_close_s.copy()
        close_copy       = self.__close_s.copy()
        momentum         = close_copy.copy()

        # Not sure which close to use.
        close_copy_this  = close_copy
        if N == None:
            N            = self.WEILDERS_CONSTANT

        for i in range(momentum.size-1, -1, -1):
            prev_i       = max(i-N, 0)
            momentum[i]  = close_copy_this[i] - close_copy_this[prev_i]

        self.__plot(momentum, ratio=hratio, frame=frame, label="momentum")

        return momentum

    def aroon_oscillator(self, N=None, hratio=1, frame=None):
        """
        Return and plot aroon oscillator.
        @args
            N            = time period in days. If not provided, default (14 days) will be assumed.
            hratio       = height ratio of the plot.
            frame        = an optional prespecified frame no
        @return
            list of aroon_up and aroon_down. aroon_up and aroon_down are of pandas.Series type.
        """
        adj_close_copy       = self.__adj_close_s.copy()
        close_copy           = self.__close_s.copy()
        
        close_copy_this      = adj_close_copy
        aroon_up             = close_copy_this.copy()
        aroon_down           = aroon_up.copy()
        list_size            = close_copy_this.size
        if N == None:
            N                = self.WEILDERS_CONSTANT

        for i in range(list_size-1, -1, -1):
            marker_a         = max(i - N + 1, 0)
            marker_b         = i + 1
            list_slice       = close_copy_this[marker_a:marker_b]

            max_this         = list_slice.max()
            min_this         = list_slice.min()
            max_index        = list_slice.tolist().index(max_this)
            min_index        = list_slice.tolist().index(min_this)

            aroon_up[i]      = float(N - 1 - max_index)/N * 100
            aroon_down[i]    = float(N - 1 - min_index)/N * 100

        frame_this           = self.__plot(aroon_up,   ratio=hratio, frame=frame, label="arun_up")
        frame_this           = self.__plot(aroon_down, ratio=hratio, frame=frame_this, label="arun_down")

        return [aroon_up, aroon_down]

    def volatility_index_single_pass(self, N):
        """
        Custom algorithm : This Volatility indicator is 1 pass and uses closing prices.
        NOTE             : Since it returns a single value, this indicator can't be plotted.
        @args
            N            = time period in days. If not provided, default (14 days) will be assumed.
        @return
            volatility indicator as a single discreet floting point value.
        """
        step_prev_list = self.stock_data["Adj Close"].copy()
        step_next_list = pandas.rolling_std(step_prev_list, N).dropna()
        return pandas.rolling_std(step_next_list, step_next_list.size)[-1]

    def volatility_index_multi_pass(self, N):
        """
        Custom algorithm : This volatility indicator is multipass and uses closing prices.
        NOTE             : Since it returns a single value, this indicator can't be plotted.
        @args
            N            = time period in days. If not provided, default (14 days) will be assumed.
        @return
            volatility indicator as a single discreet floting point value.
        """
        n = N
        step_prev_list = self.stock_data["Adj Close"].copy()
        while True:
            step_next_list = pandas.rolling_std(step_prev_list, n).dropna()
            if step_next_list.size < n:
                return step_next_list[-1]
            step_prev_list = step_next_list

    def volatility_index_multi_pass_expanding(self, N):
        """
        Custom algorithm : This volatility indicator is another version of multipass and uses closing prices.
        NOTE             : Since it returns a single value, this indicator can't be plotted.
        @args
            N            = time period in days. If not provided, default (14 days) will be assumed.
        @return
            volatility indicator as a single discreet floting point value.
        """
        n = N
        step_prev_list = self.stock_data["Adj Close"].copy()
        while True:
            step_next_list = pandas.rolling_std(step_prev_list, n).dropna()
            n = n * 2
            if step_next_list.size < n:
                return step_next_list[-1]
            step_prev_list = step_next_list

    def print_info(self):
        """Print information about this class attributes."""
        print "name = {}, date_start = {}, date_end = {}" . format(self.name, self.date_start, self.date_end)




############################################################################
# analysis class
############################################################################
class analysis_class:
    def __init__(self, params):
        assert(type(params) == parameters)
        self.params       = params
        if self.params.pickle_file_passed:
            stock_analysis_class.load_database_from_pickle(self.params.pickle_file)
            assert(type(stock_analysis_class.pickle_dict) == dict)

    def init_stock_data(self, scripid, name='default'):
        self.stock_data   = stock_analysis_class(scripid, self.params.date_start, self.params.date_end, name, self.params.plot_yes)

    def stock_analysis_instance(self):
        return self.stock_data

    def __check_price_range(self):
        close_latest      = self.stock_data.get_close()[-1]
        if self.params.price_check and (close_latest < self.params.pmin or close_latest > self.params.pmax):
            if self.params.verbose:
                print "{} has latest closing price {}, hence is not in defined price range." . format(self.stock_data.scripid, close_latest)
            return False
        return True

    def __check_volumes(self):
        av_past_vol_100   = pandas.rolling_mean(self.stock_data.get_volume(), 100)[-1]
        if self.params.volume_check and av_past_vol_100 < self.params.trade_min:
            if self.params.verbose:
                print "100 day median trade volume for {} is below {}." . format(self.stock_data.scripid, self.params.trade_min)
            return False
        return True

    def __check_trend(self):
        """
        Check current trend based on moving averages.
        """
        mov_avg_h                 = {}
        local_trend               = self.params.TICKER_TREND_TYPE_NOTA
        close_data                = self.stock_data.get_close()
        vol_data                  = self.stock_data.get_volume()
        adj_close_data            = self.stock_data.get_adj_close()
        param_mova_days_dict      = self.params.mova_days_dict
        compr_ravg_tup            = self.params.compr_ravg_tup

        # Calculate all moving averages as specified by parameters class
        for dindex in param_mova_days_dict.keys():
            mean_this                                   = pandas.rolling_mean(adj_close_data, param_mova_days_dict[dindex])
            mov_avg_h[param_mova_days_dict[dindex]]     = mean_this

        # Calculate trend
        if mov_avg_h[max(compr_ravg_tup)][-1] < mov_avg_h[min(compr_ravg_tup)][-1]:
            local_trend = self.params.TICKER_TREND_TYPE_BULLISH
        elif mov_avg_h[max(compr_ravg_tup)][-1] > mov_avg_h[min(compr_ravg_tup)][-1]:
            local_trend = self.params.TICKER_TREND_TYPE_BEARISH
        else:
            local_trend = self.params.TICKER_TREND_TYPE_NOTA

        # Trend check
        if self.params.ticker_trend == local_trend:
            print "----------------> {} shows {} trend." . format(self.stock_data.scripid, self.params.trend_tostr(local_trend))
            return True
        return False

    #def finish_plot(self):
    #    if self.params.plot_yes:
    #        show()

