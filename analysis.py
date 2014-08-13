#!/usr/bin/python

import datetime
import pickle

import pandas
import pandas.io.data
from   pandas import Series, DataFrame

import matplotlib
import matplotlib.pyplot

#################################################################
# parameters class
#################################################################
class parameters:
    """Parameters class."""
    TICKER_TREND_TYPE_FLAT       = 0
    TICKER_TREND_TYPE_BULLISH    = 1
    TICKER_TREND_TYPE_BEARISH    = 2
    TICKER_TREND_TYPE_NOTA       = 99

    ticker_trend_tostr  = {
                                 TICKER_TREND_TYPE_FLAT     : "flat",
                                 TICKER_TREND_TYPE_BULLISH  : "bullish",
                                 TICKER_TREND_TYPE_BEARISH  : "bearish",
                                 TICKER_TREND_TYPE_NOTA     : "nota"
                          }

    def __init__():
        self.ticker_trend        = 0          # 0 means no trend, 1 means upward trend, 2 means downward trend
        self.mova_days_dict      = {"20_days" : 20, "40_days" : 40, "60_days" : 60, "100_days" : 100}
        self.compr_ravg_tup      = (20, 100)
        
        self.pmin                = 10
        self.pmax                = 50
        self.trade_min           = 500000     # minium trade volume to remove less liquid stocks
        self.volume_check        = 0
        self.price_check         = 0
        self.date_start          = datetime.datetime(2014, 01, 01)
        self.date_end            = datetime.datetime.now()                # end time is current time
        self.plot_yes            = 0
        self.verbose             = 0                                      # verbose mode
        self.pickle_file_passed  = 0
        self.pickle_file         = 'default'
        self.db_file             = 'default.pkl'
        self.db_file             = 'default.txt'

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



#################################################################
# stock analysis class
#################################################################
class stock_analysis_class:
    """Analysis algorithms for stock indicators."""
    pickle_dict              = {}
    WEILDERS_CONSTANT        = 27

    def __init__(self, scripid, date_start, date_end=datetime.datetime.now(), name=''):
        self.scripid         = scripid
        self.name            = ''
        self.date_start      = date_start
        self.date_end        = date_end
        if self.name == '':
            self.name        = self.scripid

    @classmethod
    def load_database_from_pickle(cls, filename):
        cls.pickle_dict      = pickle.load(open(filename, "rb"))

    @classmethod
    def store_database_to_pickle(cls, filename):
        pickle.dump(cls.pickle_dict, open(filename, "wb"))

    def load_from_yahoo(self):
        self.stock_data      = pandas.io.data.get_data_yahoo(self.scripid, self.date_start, self.date_end)
        self.adj_close_s     = self.stock_data["Adj Close"]
        self.close_s         = self.stock_data["Close"]
        self.open_s          = self.stock_data["Open"]
        self.volume_s        = self.stock_data["Volume"]
        self.high_s          = self.stock_data["High"]
        self.low_s           = self.stock_data["Low"]

    def load_from_internal_database(self):
        self.stock_data      = pickle_dict[self.scripid]

    def moving_average(self, N):
        """Moving average for closing prices"""
        return pandas.rolling_mean(self.adj_close_s.copy(), N)

    def exponential_moving_average(self, N):
        """Exponential moving average for closing prices."""
        return pandas.ewma(self.adj_close_s.copy(), N)

    def wilders_moving_average(self):
        """Wilder's moving average."""
        return self.exponential_moving_average(27)

    # Uses adjusted closing price
    def on_balance_volume(self):
        """On balance volume."""
        adj_close_l          = self.adj_close_s.copy()
        obv_l                = self.volume_s.copy()
        obv_prev             = obv_l[0]
        close_prev           = adj_close_l[0]
        for i in range(1, obv_l.size):
            if adj_close_l[i] > close_prev:
                obv_l[i]     = obv_prev + obv_l[i]
            elif adj_close_l[i] < close_prev:
                obv_l[i]     = obv_prev - obv_l[i]
            close_prev       = adj_close_l[i]
            obv_prev         = obv_l[i]
        return obv_l

    def accumulation_distribution(self):
        """Accumulation Distribution Data"""
        obj = self.stock_data.copy()
        return (obj["Close"] - obj["Open"])/(obj["High"] - obj["Low"]) * obj["Volume"]

    def directional_movement_system(self):
        """Directional movement system as developed by Dr. Welles Wilder."""
        high_copy        = self.high_s.copy()
        low_copy         = self.low_s.copy()
        adj_close_copy   = self.adj_close_s.copy()
        close_copy       = self.close_s.copy()
        plus_dm          = self.high_s.copy()
        minus_dm         = self.low_s.copy()
        list_size        = plus_dm.size
        true_range       = minus_dm.copy()

        # Not sure which close to use.
        close_copy_this  = close_copy

        for i in range(list_size-1, 0, -1):
            plus_dm[i]      = high_copy[i] - high_copy[i-1]
            minus_dm[i]     = low_copy[i-1] - low_copy[i]
            # Insider day
            #if plus_dm[i] > 0 and minus_dm[i] > 0:
            #    pass
            true_range[i]   = max(high_copy[i] - low_copy[i], high_copy[i] - close_copy_this[i-1], close_copy_this[i-1] - low_copy[i])

        plus_dm14        = pandas.ewma(plus_dm,      self.WEILDERS_CONSTANT)
        minus_dm14       = pandas.ewma(minus_dm,     self.WEILDERS_CONSTANT)
        tr14             = pandas.ewma(true_range,   self.WEILDERS_CONSTANT)
        plus_di14        = plus_dm14/tr14
        minus_di14       = minus_dm14/tr14
        di_diff          = abs(plus_di14 - minus_di14)
        dx               = di_diff/(abs(plus_di14) + abs(minus_di14))
        adx              = pandas.ewma(dx,           self.WEILDERS_CONSTANT)

        return [plus_di14, minus_di14, adx]


    def volatility_index_single_pass(self, N):
        """This Volatility indicator is 1 pass and uses closing prices."""
        step_prev_list = self.stock_data["Adj Close"].copy()
        step_next_list = pandas.rolling_std(step_prev_list, N).dropna()
        return pandas.rolling_std(step_next_list, step_next_list.size)[-1]

    def volatility_index_multi_pass(self, N):
        """This volatility indicator is multipass and uses closing prices."""
        n = N
        step_prev_list = self.stock_data["Adj Close"].copy()
        while True:
            step_next_list = pandas.rolling_std(step_prev_list, n).dropna()
            if step_next_list.size < n:
                return step_next_list[-1]
            step_prev_list = step_next_list

    def volatility_index_multi_pass_expanding(self, N):
        """This volatility indicator is multipass and uses closing prices."""
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


###############################################################################
# new plotting class library
###############################################################################
class plots_class:
    """Customized plotting class"""
    # Plot type constants
    PLOT_TYPE_BAR      = 0
    PLOT_TYPE_PLOT     = 1

    def __init__(self, label=''):
        """Initialize a new figure object."""
        self.fig       = matplotlib.pyplot.figure(label)
        self.data      = {}
        self.n_plots   = 0
        self.n_columns = 1
        self.n_rows    = 0
        self.h_ratios  = []

    def __layout_subplots(self):
        """Create layouts."""
        plot_obj_l     = []
        x              = 0
        for i in range(0, self.n_plots):
            plot_obj_l.append(matplotlib.pyplot.subplot2grid((self.n_rows, 1), (x, 0), rowspan=self.h_ratios[i]))
            x = x + self.h_ratios[i]
        self.plot_obj  = plot_obj_l

    def __inc_plots(self):
        self.n_plots   = self.n_plots + 1

    def __append_new(self, ratio=1):
        """Make preparations for appending a new plot."""
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
    
    def __check_valid_frame(self, ratio, frame):
        """Check if the frame is valid.If not, allocate a new frame."""
        if frame == None:
            self.__append_new(ratio)
            return self.n_plots - 1
        else:
            assert(frame < self.n_plots)
            return frame

    def __append_data(self, frame, data):
        """Append the plot data structure to the object's internal database."""
        if not (frame in self.data):
            self.data[frame] = []
        self.data[frame].append(data)

    def __plot(self, obj, x_list, y_list, label):
        obj.plot(x_list, y_list, label=label)

    def __bar(self, obj, x_list, y_list, label):
        obj.bar(x_list, y_list, label=label)

    def __draw(self, frame, x_list, y_list, label, plot_type):
        """Internal plot."""
        obj_this       = self.plot_obj[frame]
        obj_this.grid()
        obj_this.set_title(label)
        if plot_type == self.PLOT_TYPE_PLOT:
            self.__plot(obj_this, x_list, y_list, label)
        elif plot_type == self.PLOT_TYPE_BAR:
            self.__bar(obj_this, x_list, y_list, label)
        self.fig.tight_layout()

    def plot(self, x_list, y_list, label='', ratio=1, frame=None):
        """Plot the actual data."""
        frame_new      = self.__check_valid_frame(ratio, frame)
        self.__draw(frame_new, x_list, y_list, label, self.PLOT_TYPE_PLOT)
        self.__append_data(frame_new,\
                  {"x_list" : x_list, "y_list" : y_list, "label" : label, "plot_type" : self.PLOT_TYPE_PLOT})
        

    def bar(self, x_list, y_list, label='', ratio=1, frame=None):
        """Plot the actual data as bars."""
        frame_new      = self.__check_valid_frame(ratio, frame)
        self.__draw(frame_new, x_list, y_list, label, self.PLOT_TYPE_BAR)
        self.__append_data(frame_new,\
                  {"x_list" : x_list, "y_list" : y_list, "label" : label, "plot_type" : self.PLOT_TYPE_BAR})

    def plot_pandas_series(self, series, label='', ratio=1, frame=None):
        """Plot pandas.core.series.Series type data."""
        assert(type(series) == pandas.core.series.Series)
        self.plot(series.index.tolist(), series.tolist(), label, ratio, frame)

    def bar_pandas_series(self, series, label='', ratio=1, frame=None):
        """Plot pandas.core.series.Series type data as bars."""
        assert(type(series) == pandas.core.series.Series)
        self.bar(series.index.tolist(), series.tolist(), label, ratio, frame)


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
        self.stock_data   = stock_analysis_class(scripid, self.params.date_start, self.params.date_end, name)


############################################################################
# wrapper over matplotlib's show()
def show():
    matplotlib.pyplot.show()
