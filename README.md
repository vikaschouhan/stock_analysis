stock_analysis
==============

stock analysis using matplotlib and pandas python libraries.
Distributed under GPLv2

Copyright 2014 Vikas Chouhan (presentisgood@gmail.com)

Steps to use
===============
0. Start ipython with --matplotlib parameter, so that plotting features are enabled.
1. From ipython import analysis.py module. Make sure it lies in a path where your python can find it.
2. Initialize stock data using analysis.stock_analysis_class. For eg.
   stock_instance = analysis.stock_analysis_class("PCJEWELLER.BO", "2014:01:01", plot=True)
                 # PCJEWELLER.BO is yahoo scrip id for PC Jewellers Ltd.
                 # "2014:01:01" is starting date.
                 # if plot is enabled, each function will go on plotting it's graph automatically.
                 # you can control placement of plots on the figure canvas using optional hratio and frame
                 # parameters.
3. Start performing techincal analysis.Examples are given below.

   closing_price          = stock_instance.closing_price()       # to get closing price. This will plot on frame 0
   moving_average_10days  = stock_instance.moving_average(10)    # 10 days moving average. This will plot on frame 1
                                                                 # thus creating two subplots on the same figure.

   To get moving average's plot drawn on same frame as that of closing price, call
   moving_average_10days  = stock_instance.moving_average(10, frame=0) # Now this will plot on frame 0
