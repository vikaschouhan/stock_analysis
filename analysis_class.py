#!/usr/bin/python

import datetime
import pandas
import pandas.io.data
from   pandas import Series, DataFrame

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
