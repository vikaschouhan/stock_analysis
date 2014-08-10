#!/usr/bin/python

import datetime
import pandas
import pandas.io.data
from   pandas import Series, DataFrame

import matplotlib

class analysis_class:
    'Analysis algorithms for stock indicators'

    def __init__(self, scripid, date_start, date_end=datetime.datetime.now(), name=''):
        self.scripid         = scripid
        self.name            = ''
        self.date_start      = date_start
        self.date_end        = date_end
        self.stock_info      = pandas.io.data.get_data_yahoo(self.scripid, self.date_start, self.date_end)

        if self.name == '':
            self.name = self.scripid

    def moving_average(self, N):
        """Moving average for closing prices"""
        return pandas.rolling_mean(self.stock_info["Adj Close"], N)

    def accumulation_distribution(self):
        """Accumulation Distribution Data"""
        obj = self.stock_info.copy()
        return (obj["Close"] - obj["Open"])/(obj["High"] - obj["Low"]) * obj["Volume"]

    def volatility_index_single_pass(self, N):
        """This Volatility indicator is 1 pass and uses closing prices."""
        step_prev_list = self.stock_info["Adj Close"].copy()
        step_next_list = pandas.rolling_std(step_prev_list, N).dropna()
        return pandas.rolling_std(step_next_list, step_next_list.size)[-1]

    def volatility_index_multi_pass(self, N):
        """This volatility indicator is multipass and uses closing prices."""
        n = N
        step_prev_list = self.stock_info["Adj Close"].copy()
        while True:
            step_next_list = pandas.rolling_std(step_prev_list, n).dropna()
            if step_next_list.size < n:
                return step_next_list[-1]
            step_prev_list = step_next_list

    def volatility_index_multi_pass_expanding(self, N):
        """This volatility indicator is multipass and uses closing prices."""
        n = N
        step_prev_list = self.stock_info["Adj Close"].copy()
        while True:
            step_next_list = pandas.rolling_std(step_prev_list, n).dropna()
            n = n * 2
            if step_next_list.size < n:
                return step_next_list[-1]
            step_prev_list = step_next_list

    def print_info(self):
        """Print information about this class attributes."""
        print "name = {}, date_start = {}, date_end = {}" . format(self.name, self.date_start, self.date_end)




class plots_class:
    'Customized plotting class'
    def __init__(self, n_plots, height_ratios, label=''):
        """Initialize a figure object. n_plots is the total number plots on this figure. \
                height_ratios is a tuple/list of the corresponding height ratios.The ratios should be integers only"""
        assert(type(height_ratios) == tuple or type(height_ratios) == list)
        assert(len(height_ratios) == n_plots)

        height_ratios = map(int, height_ratios)
        fig           = matplotlib.pyplot.figure(label)
        n_rows        = sum(height_ratios)
        plot_obj_l    = []
        x             = 0

        for i in range(0, n_plots):
            plot_obj_l.append(matplotlib.pyplot.subplot2grid((n_rows, 1), (x, 0), rowspan=height_ratios[i]))
            x = x + height_ratios[i]

        self.plot_obj  = plot_obj_l
        self.fig       = fig
        self.n_plots   = n_plots
        self.n_rows    = n_rows
        self.n_columns = 1
        self.plotted   = 0

    def __inc_plotted(self):
        self.plotted   = self.plotted + 1

    def plot(self, x_list, y_list, label=''):
        """Plot the actual data."""
        assert(self.plotted < self.n_plots)

        obj_this       = self.plot_obj[self.plotted]
        obj_this.grid()
        obj_this.set_title(label)
        obj_this.plot(x_list, y_list)
        self.__inc_plotted()

    def bar(self, x_list, y_list, label=''):
        """Plot the actual data as bars."""
        assert(self.plotted < self.n_plots)

        obj_this       = self.plot_obj[self.plotted]
        obj_this.grid()
        obj_this.set_title(label)
        obj_this.bar(x_list, y_list)
        self.__inc_plotted()

    def plot_pandas_series(self, series, label=''):
        """Plot pandas.core.series.Series type data."""
        assert(type(series) == pandas.core.series.Series)
        self.plot(series.index.tolist(), series.tolist(), label)

    def bar_pandas_series(self, series, label=''):
        """Plot pandas.core.series.Series type data as bars."""
        assert(type(series) == pandas.core.series.Series)
        self.bar(series.index.tolist(), series.tolist(), label)

