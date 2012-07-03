# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name			 	 : GEM Modellers Toolkit plugin (GEM-MT)
Description          : Analysing and Processing Earthquake Catalogue Data
Date                 : Jun 21, 2012 
copyright            : (C) 2012 by Giuseppe Sucameli (Faunalia)
email                : brush.tyler@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# Python Qt4 bindings for GUI objects
from PyQt4 import QtGui, QtCore

# Numpy functions for image creation
import numpy as np

# Matplotlib Figure object
from matplotlib.figure import Figure

import itertools
from matplotlib.dates import date2num
from datetime import datetime
from pylab import *

# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

class PlotWdg(FigureCanvas):
	"""Class to represent the FigureCanvas widget"""
	def __init__(self, xValues, yValues, xLabel, yLabel, title=None, props=None):

		self.x, self.y = xValues, yValues
		self.xLabel, self.yLabel = xLabel, yLabel
		self.title = title
		self.props = props if isinstance(props, dict) else {}

		self.fig = Figure()
		self.axes = self.fig.add_subplot(111)

		self.axes.set_xlabel( self.xLabel )
		self.axes.set_ylabel( self.yLabel )
		if self.title and self.title != "":
			self.axes.set_title( self.title )

		yscale = self.props.get('yscale', None)
		if yscale:
			self.axes.set_yscale( yscale )

		self._plot()

		# initialize the canvas where the Figure renders into
		FigureCanvas.__init__(self, self.fig)

	def _plot(self):
		pass

	@staticmethod
	def _valueFromQVariant(val):
		""" function to convert values to proper types """
		if not isinstance(val, QtCore.QVariant):
			return val

		def convertToDate( s ):
			try:
				return datetime.strptime(unicode(s), '%Y-%m-%d %H:%M:%S')
			except ValueError:
				pass

			return datetime.strptime(unicode(s), '%Y-%m-%d')

		if val.type() == QtCore.QVariant.Int:
			return val.toInt()[0]
		elif val.type() == QtCore.QVariant.Double:
			return val.toDouble()[0]

		if val.type() == QtCore.QVariant.Date:
			return convertToDate( val.toDate().toString("yyyy-MM-dd") )

		elif val.type() == QtCore.QVariant.DateTime:
			return convertToDate( val.toDateTime().toString("yyyy-MM-dd hh:mm:ss") )

		s = val.toString()
		# try to convert the string to a date
		try:
			return convertToDate( s )
		except ValueError:
			pass

		return unicode(s)


class HistogramPlotWdg(PlotWdg):

	def __init__(self, *argv):
		super(HistogramPlotWdg, self).__init__(*argv)

	def _plot(self):
		# convert values, then create the plot
		x = map(PlotWdg._valueFromQVariant, self.x)

		if isinstance(x[0], datetime): 
			timedelta = max(x) - min(x)
			if timedelta.days > 365:
				self.axes.xaxis.set_major_locator( YearLocator() )
				self.axes.xaxis.set_major_formatter( DateFormatter('%Y') )
				self.axes.xaxis.set_minor_locator( MonthLocator() )
				#bins = timedelta.days * 4 / 356	# four bins for a year

			elif timedelta.days > 30:
				self.axes.xaxis.set_major_locator( MonthLocator() )
				self.axes.xaxis.set_major_formatter( DateFormatter('%Y-%m') )
				self.axes.xaxis.set_minor_locator( DayLocator() )
				#bins = timedelta.days * 4 / 30	# four bins for a month

			else:
				self.axes.xaxis.set_major_locator( DayLocator() )
				self.axes.xaxis.set_major_formatter( DateFormatter('%Y-%m-%d') )
				#self.axes.xaxis.set_minor_locator( HourLocator() )
				#bins = timedelta.days * 4	# four bins for a day

			self.axes.hist(date2num(x), bins=50)
			self.fig.autofmt_xdate()

		else:
			self.axes.hist(x, bins=50)


class ScatterPlotWdg(PlotWdg):

	def __init__(self, *argv):
		super(ScatterPlotWdg, self).__init__(*argv)

	def _plot(self):
		# convert values, then create the plot
		x = map(PlotWdg._valueFromQVariant, self.x)
		y = map(PlotWdg._valueFromQVariant, self.y)

		if isinstance(x[0], datetime): 
			timedelta = max(x) - min(x)
			if timedelta.days > 365:
				self.axes.xaxis.set_major_locator( YearLocator() )
				self.axes.xaxis.set_major_formatter( DateFormatter('%Y') )
				self.axes.xaxis.set_minor_locator( MonthLocator() )
				#bins = timedelta.days * 4 / 356	# four bins for a year

			elif timedelta.days > 30:
				self.axes.xaxis.set_major_locator( MonthLocator() )
				self.axes.xaxis.set_major_formatter( DateFormatter('%Y-%m') )
				self.axes.xaxis.set_minor_locator( DayLocator() )
				#bins = timedelta.days * 4 / 30	# four bins for a month

			else:
				self.axes.xaxis.set_major_locator( DayLocator() )
				self.axes.xaxis.set_major_formatter( DateFormatter('%Y-%m-%d') )
				#self.axes.xaxis.set_minor_locator( HourLocator() )
				#bins = timedelta.days * 4	# four bins for a day

			self.axes.plot_date(x, y)
			self.fig.autofmt_xdate()

		else:
			self.axes.scatter(x, y)



if __name__ == "__main__":
	# for command-line arguments
	import sys

	# Create the GUI application
	app = QtGui.QApplication(sys.argv)

	# Create the Matplotlib widget
	mpl = HistogramPlotWdg([1,2,3,4,5], "x", "y")
	# show the widget
	mpl.show()

	# start the Qt main loop execution, exiting from this script
	# with the same return code of Qt application
	sys.exit(app.exec_())

