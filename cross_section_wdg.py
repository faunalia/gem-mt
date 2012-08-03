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

from PyQt4 import QtGui, QtCore

from .plot_wdg import PlotDlg, PlotWdg, NavigationToolbar, ClippedLine2D
import resources_rc

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

			px, py = point
			info = self.plot.info[index]

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


if __name__ == "__main__":
	# for command-line arguments
	import sys

	# Create the GUI application
	app = QtGui.QApplication(sys.argv)

	# show a cross-section plot
	CrossSectionWdg( ([1,2,3,4,5],[10,9,7,4,0]), labels=("x", "y"), title="Cross section" ).show()

	# start the Qt main loop execution, exiting from this script
	# with the same return code of Qt application
	sys.exit(app.exec_())

