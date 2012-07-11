# -*- coding: utf-8 -*-

"""
/****************************************************************************
Name			 	: GEM Modellers Toolkit plugin (GEM-MT)
Description			: Analysing and Processing Earthquake Catalogue Data
Date				: Jun 21, 2012 
copyright			: (C) 2012 by Giuseppe Sucameli (Faunalia)
email				: brush.tyler@gmail.com
 ****************************************************************************/

/****************************************************************************
 *																			*
 *	This program is free software; you can redistribute it and/or modify	*
 *	it under the terms of the GNU General Public License as published by	*
 *	the Free Software Foundation; either version 2 of the License, or		*
 *	(at your option) any later version.										*
 *																			*
 ****************************************************************************/
"""

# Python Qt4 bindings for GUI objects
from PyQt4 import QtGui, QtCore

# Matplotlib Figure object
from matplotlib.figure import Figure

from matplotlib.dates import date2num
from datetime import datetime

from pylab import Line2D, YearLocator, MonthLocator, DayLocator, DateFormatter

# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg

class PlotWdg(FigureCanvasQTAgg):
	"""Class to represent the FigureCanvas widget"""
	def __init__(self, data=None, labels=None, title=None, props=None):

		self.fig = Figure()
		self.axes = self.fig.add_subplot(111)

		# initialize the canvas where the Figure renders into
		FigureCanvasQTAgg.__init__(self, self.fig)

		self._dirty = False
		self.collections = []

		if not data: data = []
		self.setData( data[0] if len(data) > 0 else None, data[1] if len(data) > 1 else None, data[2] if len(data) > 2 else None )

		if not labels: labels = []
		self.setLabels( labels[0] if len(labels) > 0 else None, labels[1] if len(labels) > 1 else None )

		self.setTitle( title )

		self.props = props if isinstance(props, dict) else {}

		yscale = self.props.get('yscale', None)
		if yscale:
			self.axes.set_yscale( yscale )


	def itemAt(self, index):
		if index >= len(self.x):
			return None
		return (self.x[index] if self.x else None, self.y[index] if self.y else None, self.info[index] if self.info else None)


	def delete(self):
		self._clear()

		# unset delete function
		self.delete = lambda: None

	def __del__(self):
		self.delete()

	def deleteLater(self, *args):
		self.delete()
		return FigureCanvasQTAgg.deleteLater(self, *args)
		
	def destroy(self, *args):
		self.delete()
		return FigureCanvasQTAgg.destroy(self, *args)


	def setDirty(self, val):
		self._dirty = val

	def showEvent(self, event):
		if self._dirty:
			self.refreshData()
		return FigureCanvasQTAgg.showEvent(self, event)


	def refreshData(self):
		# remove the old stuff
		self._clear()
		# plot the new data
		self._plot()
		# udpdate axis limits
		self.axes.relim()	# it doesn't shrink until removing all the objects on the axis
		# re-draw
		self.draw()
		# unset the dirty flag
		self._dirty = False


	def setData(self, x, y, info=None):
		self.x, self.y = x or [], y or []
		self.info = info or []
		self._dirty = True

	def setTitle(self, title):
		self.axes.set_title( title or "" )

	def setLabels(self, xLabel, yLabel):
		self.axes.set_xlabel( xLabel or "" )
		self.axes.set_ylabel( yLabel or "" )

	def _clear(self):
		for item in self.collections:
			try:
				item.remove()
			except AttributeError:
				pass

		self.collections = []

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

	def __init__(self, *args, **kwargs):
		PlotWdg.__init__(self, *args, **kwargs)

	def _plot(self):
		# convert values, then create the plot
		x = map(PlotWdg._valueFromQVariant, self.x)

		if isinstance(x[0], datetime): 
			timedelta = max(x) - min(x)
			if timedelta.days > 365*5:
				self.axes.xaxis.set_major_formatter( DateFormatter('%Y') )
				#self.axes.xaxis.set_major_locator( YearLocator() )
				#self.axes.xaxis.set_minor_locator( MonthLocator() )
				#bins = timedelta.days * 4 / 356	# four bins for a year

			elif timedelta.days > 30*5:
				self.axes.xaxis.set_major_formatter( DateFormatter('%Y-%m') )
				#self.axes.xaxis.set_major_locator( MonthLocator() )
				#self.axes.xaxis.set_minor_locator( DayLocator() )
				#bins = timedelta.days * 4 / 30	# four bins for a month

			else:
				self.axes.xaxis.set_major_formatter( DateFormatter('%Y-%m-%d') )
				#self.axes.xaxis.set_major_locator( DayLocator() )
				#self.axes.xaxis.set_minor_locator( HourLocator() )
				#bins = timedelta.days * 4	# four bins for a day

			n, bins, patches = self.axes.hist(date2num(x), bins=50)
			self.fig.autofmt_xdate()

		else:
			n, bins, patches = self.axes.hist(x, bins=50)

		self.collections.append( patches )


class ScatterPlotWdg(PlotWdg):

	def __init__(self, *args, **kwargs):
		PlotWdg.__init__(self, *args, **kwargs)

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

			items = self.axes.plot_date(x, y)
			self.fig.autofmt_xdate()

		else:
			items = self.axes.scatter(x, y)

		self.collections.append( items )


class PlotDlg(QtGui.QDialog):
	def __init__(self, *args, **kwargs):
		QtGui.QDialog.__init__(self, kwargs.get('parent', None), QtCore.Qt.Window)
		self.setWindowTitle("Plot dialog")

		layout = QtGui.QVBoxLayout(self)

		self.plot = self.createPlot()
		layout.addWidget(self.plot)

		self.nav = self.createToolBar()
		layout.addWidget(self.nav)


	def enterEvent(self, event):
		self.nav.set_cursor( NavigationToolbar.Cursor.POINTER )
		return QtGui.QDialog.enterEvent(self, event)

	def leaveEvent(self, event):
		self.nav.unset_cursor()
		return QtGui.QDialog.leaveEvent(self, event)

	def createPlot(self):
		raise ValueError("invalid or missing plot type")

	def createToolBar(self):
		return NavigationToolbar(self.plot, self)


	def refresh(self):
		# query for refresh
		self.plot.setDirty(True)

		if self.isVisible():
			# refresh if it's already visible
			self.plot.refreshData()

	def setData(self, x, y, data=None):
		self.plot.setData(x, y, data)

	def setTitle(self, title):
		self.plot.setTitle(title)

	def setLabels(self, xLabel, yLabel):
		self.plot.setLabels(xLabel, yLabel)



class HistogramPlotDlg(PlotDlg):
	def __init__(self, *args, **kwargs):
		self._args, self._kwargs = args, kwargs
		PlotDlg.__init__(self, parent=kwargs.get('parent', None))

	def createPlot(self):
		return HistogramPlotWdg(*self._args, **self._kwargs)

class ScatterPlotDlg(PlotDlg):
	def __init__(self, *args, **kwargs):
		self._args, self._kwargs = args, kwargs
		PlotDlg.__init__(self, parent=kwargs.get('parent', None))

	def createPlot(self):
		return ScatterPlotWdg(*self._args, **self._kwargs)


class CrossSectionDlg(PlotDlg):

	def __init__(self, classificationMap, parent=None):
		self._classificationMap = classificationMap

		PlotDlg.__init__(self, parent=parent)

		self.connect(self.nav, QtCore.SIGNAL("classificationUpdateRequested"), self.updateClassification)


	def createPlot(self):
		return CrossSectionGraph( self._classificationMap )

	def createToolBar(self):
		return NavigationToolbarCrossSection(self.plot, self)


	def closeEvent(self, event):
		self.updateClassification()
		return QtGui.QDialog.closeEvent(self, event)

		
	def updateClassification(self):
		self.emit( QtCore.SIGNAL("classificationUpdateRequested") )

	def classify(self):
		hy = self.plot.hline.get_ydata()[0]

		(ox0,ox1),(oy0,oy1) = self.plot.oline.get_data()
		if ox1 == ox0:
			ocoeff = None	# the oblique line is a vertical line...
		else:
			ocoeff = float(oy1 - oy0) / (ox1 - ox0)
		
		# classify earthquakes and discard indeterminate ones 
		shallow, deep = [], []
		for index in range(len(self.plot.x)):
			point = self.plot.itemAt(index)
			if not point:
				continue
			px, py, info = point

			if py > hy:
				shallow.append( info )
			elif ocoeff == None:
				if px <= ox0:
					deep.append( info )
			else:
				y = ocoeff * (px - ox0) + oy0
				if py <= y:
					deep.append( info )

		return (shallow, deep)


class CrossSectionGraph(PlotWdg):

	def __init__(self, classificationMap, *args, **kwargs):
		PlotWdg.__init__(self,	*args, **kwargs)
		self._classificationMap = classificationMap

		self.hline = self.axes.axhline(y=0, lw=3., color='b', alpha=0.4)

		self.oline = ClippedLine2D((0,0), (0,1), lw=3., color='r', alpha=0.4)
		self.axes.add_line(self.oline)

	def _plot(self):
		# convert values, then create the plot
		x = map(PlotWdg._valueFromQVariant, self.x)
		y = map(PlotWdg._valueFromQVariant, self.y)

		# split values in 3 classes: shallow, deep and unclassified earthquakes
		classes = (shallow, deep, unclassified) = ( ([],[]), ([],[]), ([],[]) )
		for index in range(len(self.x)):
			fid = self.info[index]
			if not self._classificationMap.has_key( fid ):
				classData = classes[2]	# unclassified
			else:
				classData = classes[ self._classificationMap[ fid ] ]
			classData[0].append( self.x[index] )
			classData[1].append( self.y[index] )
		
		# plot the both the earthquakes classes
		if shallow[0] and shallow[1]:
			shallowItems = self.axes.scatter(shallow[0], shallow[1], marker='o', c='r')
			self.collections.append( shallowItems )

		if deep[0] and deep[1]:
			deepItems = self.axes.scatter(deep[0], deep[1], marker='o', c='b')
			self.collections.append( deepItems )

		if unclassified[0] and unclassified[1]:
			unclassifiedItems = self.axes.scatter(unclassified[0], unclassified[1], marker='x', c='k')
			self.collections.append( unclassifiedItems )


# import the NavigationToolbar Qt4Agg widget
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg

class NavigationToolbar(NavigationToolbar2QTAgg):

	def __init__(self, *args, **kwargs):
		NavigationToolbar2QTAgg.__init__(self, *args, **kwargs)

		self.init_buttons()
		self.panAction.setCheckable(True)
		self.zoomAction.setCheckable(True)

		# remove the subplots action
		self.removeAction( self.subplotsAction )

	class Cursor:
		# cursors defined in backend_bases (from matplotlib source code)
		HAND, POINTER, SELECT_REGION, MOVE = range(4)

		@classmethod
		def toQCursor(self, cursor):
			if cursor == self.MOVE:
				n = QtCore.Qt.SizeAllCursor
			elif cursor == self.HAND:
				n = QtCore.Qt.PointingHandCursor
			elif cursor == self.SELECT_REGION:
				n = QtCore.Qt.CrossCursor
			else:#if cursor == self.POINTER:
				n = QtCore.Qt.ArrowCursor
			return QtGui.QCursor( n )

	def set_cursor(self, cursor):
		if cursor != self._lastCursor:
			self.unset_cursor()
			QtGui.QApplication.setOverrideCursor( NavigationToolbar.Cursor.toQCursor(cursor) )
			self._lastCursor = cursor

	def unset_cursor(self):
		if self._lastCursor:
			QtGui.QApplication.restoreOverrideCursor()
			self._lastCursor = None

	def init_buttons(self):
		self.homeAction = self.panAction = self.zoomAction = self.subplotsAction = None

		for a in self.actions():
			if a.text() == 'Home':
				self.homeAction = a
			elif a.text() == 'Pan':
				self.panAction = a
			elif a.text() == 'Zoom':
				self.zoomAction = a
			elif a.text() == 'Subplots':
				self.subplotsAction = a

	def resetActionsState(self, skip=None):
		# reset the buttons state
		for a in self.actions():
			if skip and a == skip:
				continue
			a.setChecked( False )

	def pan( self, *args ):
		self.resetActionsState( self.panAction )
		NavigationToolbar2QTAgg.pan( self, *args )

	def zoom( self, *args ):
		self.resetActionsState( self.zoomAction )
		NavigationToolbar2QTAgg.zoom( self, *args )


import resources_rc

class NavigationToolbarCrossSection(NavigationToolbar):
	def __init__(self, canvas, parent=None):
		NavigationToolbar.__init__(self, canvas, parent)

		# add toolbutton to the draw horizontal line
		self.hLineAction = QtGui.QAction( QtGui.QIcon(":/gem-mt_plugin/icons/hline"), "Draw horizontal line", self )
		self.hLineAction.setToolTip( "Draw horizontal line" )
		self.hLineAction.setCheckable(True)
		self.insertAction(self.homeAction, self.hLineAction)
		self.connect(self.hLineAction, QtCore.SIGNAL("triggered()"), self.drawHLine)

		# add toolbutton to the draw oblique line
		self.oLineAction = QtGui.QAction( QtGui.QIcon(":/gem-mt_plugin/icons/oline"), "Draw oblique line", self )
		self.oLineAction.setToolTip( "Draw oblique line" )
		self.oLineAction.setCheckable(True)
		self.insertAction(self.homeAction, self.oLineAction)
		self.connect(self.oLineAction, QtCore.SIGNAL("triggered()"), self.drawOLine)

		# add toolbutton to update the classification
		self.updateClassificationAction = QtGui.QAction( QtGui.QIcon(":/gem-mt_plugin/icons/refresh"), "Update classification", self )
		self.updateClassificationAction.setToolTip( "Update classification" )
		self.insertAction(self.homeAction, self.updateClassificationAction)
		self.connect(self.updateClassificationAction, QtCore.SIGNAL("triggered()"), self.updateClassification)

		self.insertSeparator(self.homeAction)

		# used in the mouse event handler
		self._startPoint = None
		self._idMotion = None


	def configure_subplots(self, *args):
		pass	# do nothing

	def updateClassification(self):
		self.emit( QtCore.SIGNAL("classificationUpdateRequested") )

	def drawHLine(self):
		if not self.hLineAction.isChecked():
			self.stopMouseCapture()
			self._active = None
			self.mode = ''
			self.set_message(self.mode)
			return

		self.resetActionsState(self.hLineAction)
		self.startMouseCapture()

		self._active = 'HLINE'
		self.mode = 'draw horizontal line'
		self.set_message(self.mode)

	def drawOLine(self):
		if not self.oLineAction.isChecked():
			self.stopMouseCapture()
			self._active = None
			self.mode = ''
			self.set_message(self.mode)
			return

		self.resetActionsState(self.oLineAction)
		self.startMouseCapture()

		self._active = 'OLINE'
		self.mode = 'draw oblique line'
		self.set_message(self.mode)

	def startMouseCapture(self):
		# remove old handlers
		self.stopMouseCapture()

		# set new handlers
		if not self._idPress:
			self._idPress = self.canvas.mpl_connect('button_press_event', self.onMousePress)
		if not self._idRelease:
			self._idRelease = self.canvas.mpl_connect('button_release_event', self.onMouseRelease)
		if not self._idMotion:
			self._idMotion = self.canvas.mpl_connect('motion_notify_event', self.onMouseMove)

	def stopMouseCapture(self):
		if self._idPress:
			self.canvas.mpl_disconnect(self._idPress)
			self._idPress = None
		if self._idRelease:
			self.canvas.mpl_disconnect(self._idRelease)
			self._idRelease = None
		if self._idMotion:
			self.canvas.mpl_disconnect(self._idMotion)
			self._idMotion = None


	def onMousePress(self, event):
		if event.inaxes != self.canvas.axes: return

		self._startPoint = event.xdata, event.ydata

		if self._active == 'HLINE':
			# move the horizontal line
			self.canvas.hline.set_ydata([event.ydata, event.ydata])
			self.canvas.draw()

	def onMouseRelease(self, event):
		self._startPoint = None
		
		#self.stopMouseCapture()
		#self.resetActionsState()

		#self._active = None
		#self.mode = ''
		#self.set_message(self.mode)

		self.canvas.draw()


	def onMouseMove(self, event):
		# override the cursor
		if event.inaxes and self._active in ['HLINE', 'OLINE']:
			self.set_cursor( NavigationToolbar.Cursor.SELECT_REGION )

		if not self._startPoint: return
		if event.inaxes != self.canvas.axes: return

		# create or update the line
		if self._active == 'HLINE':
			# move the horizontal line
			self.canvas.hline.set_ydata([event.ydata, event.ydata])

		else:
			# oblique line
			x0, y0 = self._startPoint

			xlim = self.canvas.axes.get_xlim()
			ylim = self.canvas.axes.get_ylim()

			# adjust line angle, the line is valid only from UL to BR
			dx = (event.xdata - x0)
			dy = (event.ydata - y0)

			if (dx >= 0 and dy <= 0) or (dx <= 0 and dy >= 0):
				x1, y1 = event.xdata, event.ydata
			elif abs(dx * (ylim[1]-ylim[0])) <= abs(dy * (xlim[1]-xlim[0])):
				x1, y1 = x0, event.ydata
			else:
				x1, y1 = event.xdata, y0

			self.canvas.oline.set_data( (x0,x1), (y0,y1) )

		# re-draw
		self.canvas.draw()


class ClippedLine2D(Line2D):
	"""
	Clip the xlimits to the axes view limits
	"""

	def __init__(self, *args, **kwargs):
		Line2D.__init__(self, *args, **kwargs)

	def draw(self, renderer):
		x, y = self.get_data()

		if len(x) == 2 or len(y) == 2:
			xlim = self.axes.get_xlim()
			ylim = self.axes.get_ylim()

			x0, y0 = x[0], y[0]
			x1, y1 = x[1], y[1]

			if x0 == x1:	# vertical
				x, y = (x0, x0), ylim
			elif y0 == y1:
				x, y = xlim, (y0, y0)
			else:
				coeff = float(y1 - y0) / (x1 - x0)
				minx = (ylim[0] - y0) / coeff + x0
				maxx = (ylim[1] - y0) / coeff + x0
				miny = coeff * (xlim[0] - x0) + y0
				maxy = coeff * (xlim[1] - x0) + y0

				# swap values if in the wrong position (coeff < 0)
				if minx > maxx : minx, maxx = maxx, minx
				if miny > maxy : miny, maxy = maxy, miny

				x = min(maxx, xlim[1]), max(minx, xlim[0])
				y = max(miny, ylim[0]), min(maxy, ylim[1])

			self.set_data(x, y)

		Line2D.draw(self, renderer)


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

