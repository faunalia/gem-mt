# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name			 	 : GEM Modellers Toolkit plugin (GEM-MT)
Description          : Analysing and Processing Earthquake Catalogue Data
Date                 : Jun 18, 2012 
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

class FilterDock(QDockWidget):
	def __init__(self, iface, vl, parent=None):
		QDockWidget.__init__(self, parent)

		self.mainWidget = FilterWdg(iface, vl, self)
		self.setupUi()

	def closeEvent(self, event):
		self.mainWidget.clear()

		self.emit( SIGNAL( "closed" ), self )
		return QDockWidget.closeEvent(self, event)

	def deleteLater(self):
		self.mainWidget.deleteLater()
		return QDockWidget.deleteLater(self)

	def setupUi(self):
		self.setWindowTitle( "Filter/Plot panel" )
		self.setObjectName( "gem_mt_filter_dockwidget" )
		self.setWidget( self.mainWidget )


from ui.filterWdg_ui import Ui_FilterWdg
from MapTools import PolygonDrawer

class FilterWdg(QWidget, Ui_FilterWdg):

	PLOT_HIST, PLOT_HIST_LOG, PLOT_SCATTER = range(3)

	def __init__(self, iface, vl, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi(self)

		# store the passed vars
		self.iface = iface
		self.vl = vl

		self.canvas = self.iface.mapCanvas()
		self._prevMapTool = None

		# setup the magnitude, depth and range filters
		self.magnitudeRangeFilter.setEnabled(False)
		self.depthRangeFilter.setEnabled(False)
		self.dateRangeFilter.setEnabled(False)

		self.magnitudeRangeFilter.setDecimals( 1 )
		self.magnitudeRangeFilter.setOrientation( Qt.Horizontal )
		self.magnitudeRangeFilter.setMinimum( 0 )
		self.magnitudeRangeFilter.setMaximum( 10 )
		self.magnitudeRangeFilter.setHighValue( 10 )

		self.depthRangeFilter.setOrientation( Qt.Horizontal )
		self.dateRangeFilter.setOrientation( Qt.Horizontal )

		# take min/max values index from the data provider
		fields = self.vl.dataProvider().fields()
		for index, field in fields.iteritems():
			filterWdg = self.filterForField( field.name() )
			if not filterWdg:
				continue

			filterWdg.setEnabled(True)

			minVal = self.vl.dataProvider().minimumValue( index )
			maxVal = self.vl.dataProvider().maximumValue( index )

			if filterWdg == self.dateRangeFilter:
				if minVal.isValid():
					self.dateRangeFilter.setMinimum( minVal.toDate() )
					self.dateRangeFilter.setLowValue( minVal.toDate() )
				if maxVal.isValid():
					self.dateRangeFilter.setMaximum( maxVal.toDate() )
					self.dateRangeFilter.setHighValue( maxVal.toDate() )

			elif filterWdg == self.depthRangeFilter:
				if minVal.isValid():
					self.depthRangeFilter.setMinimum( minVal.toInt()[0] )
					self.depthRangeFilter.setLowValue( minVal.toInt()[0] )
				if maxVal.isValid():
					self.depthRangeFilter.setMaximum( maxVal.toInt()[0] )
					self.depthRangeFilter.setHighValue( maxVal.toInt()[0] )

			elif False:# filterWdg == self.magnitudeRangeFilter:
				if minVal.isValid():
					self.magnitudeRangeFilter.setMinimum( minVal.toDouble()[0] )
					self.magnitudeRangeFilter.setLowValue( minVal.toDouble()[0] )
				if maxVal.isValid():
					self.magnitudeRangeFilter.setMaximum( maxVal.toDouble()[0] )
					self.magnitudeRangeFilter.setHighValue( maxVal.toDouble()[0] )


		# create the maptool to draw polygons
		self.polygonDrawer = PolygonDrawer( self.canvas, {'color':QColor("black"), 'enableSnap':False, 'keepAfterEnd':True} )
		self.polygonDrawer.setAction( self.drawPolygonBtn )
		self.connect(self.polygonDrawer, SIGNAL("geometryEmitted"), self.polygonCreated)

		# populate plot type combo
		self.plotTypeCombo.addItem( "Histogram", self.PLOT_HIST )
		self.plotTypeCombo.addItem( "Histogram (log10)", self.PLOT_HIST_LOG )
		self.plotTypeCombo.addItem( "Scatter plot", self.PLOT_SCATTER )
		self.updateAxesCombos()

		# populate both axis combos with field names
		for index, field in self.vl.dataProvider().fields().iteritems():
			self.xAxisCombo.addItem( field.name(), QVariant(index) )
			self.yAxisCombo.addItem( field.name(), QVariant(index) )

		# connect actions to the widgets
		self.connect(self.drawPolygonBtn, SIGNAL("clicked()"), self.drawPolygon)
		self.connect(self.clearPolygonBtn, SIGNAL("clicked()"), self.clearPolygon)
		self.connect(self.plotBtn, SIGNAL("clicked()"), self.plot)
		self.connect(self.plotTypeCombo, SIGNAL("currentIndexChanged(int)"), self.updateAxesCombos)


	def storePrevMapTool(self):
		prevMapTool = self.canvas.mapTool()
		if prevMapTool not in (self.polygonDrawer,):
			self._prevMapTool = prevMapTool

	def restorePrevMapTool(self):
		if self._prevMapTool: 
			self.canvas.setMapTool(self._prevMapTool)


	def _hasPlotYField(self, plotType):
		return plotType not in (self.PLOT_HIST, self.PLOT_HIST_LOG)

	def _getPlotType(self):
		return self.plotTypeCombo.itemData( self.plotTypeCombo.currentIndex() )

	def updateAxesCombos(self):
		self.yAxisCombo.setEnabled( self._hasPlotYField( self._getPlotType() ) )


	def clear(self):
		self.clearPolygon()

	def deleteLater(self):
		# restore the previous maptool
		self.polygonDrawer.stopCapture()
		self.restorePrevMapTool()

		# delete the polygon drawer maptool
		self.polygonDrawer.reset()
		self.polygonDrawer.deleteLater()
		self.polygonDrawer = None

		return QWidget.deleteLater(self)


	def drawPolygon(self):
		# store the previous maptool
		self.storePrevMapTool()

		# set the polygon drawer as current maptool
		self.polygonDrawer.startCapture()

	def clearPolygon(self):
		# remove the displayed polygon
		self.polygonDrawer.reset()

	def polygonCreated(self, polygon):
		# restore the previous maptool
		self.polygonDrawer.stopCapture()
		self.restorePrevMapTool()

	def filterForField(self, fieldName):
		from settingsDlg import Settings
		if fieldName.startsWith( Settings.magnitudeField(), Qt.CaseInsensitive ):
			return self.magnitudeRangeFilter
		if fieldName.startsWith( Settings.depthField(), Qt.CaseInsensitive ):
			return self.depthRangeFilter
		if fieldName.startsWith( Settings.dateField(), Qt.CaseInsensitive ):
			return self.dateRangeFilter
		return None

	def plot(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			self._createPlot()
		finally:
			QApplication.restoreOverrideCursor()


	def _createPlot(self):
		# the following lists will contain x and y values
		x = []
		y = []

		plotType = self._getPlotType()
		hasYField = self._hasPlotYField( plotType )

		# spatial filter
		geom = self.polygonDrawer.geometry()
		if not geom:
			extent = QgsRectangle()
		else:
			extent = geom.boundingBox()

		# get the indexes of fields selected in the combos
		xIndex = self.xAxisCombo.itemData( self.xAxisCombo.currentIndex() ).toInt()[0]
		yIndex = self.yAxisCombo.itemData( self.yAxisCombo.currentIndex() ).toInt()[0]

		pr = self.vl.dataProvider()
		fields = pr.fields()

		indexes = []
		for index, field in fields.iteritems():
			if index == xIndex:
				indexes.append( xIndex )
				continue

			if index == yIndex and hasYField:
				indexes.append( yIndex )
				continue

			filterWdg = self.filterForField( field.name() )
			if filterWdg and filterWdg.isActive():
				indexes.append( index )


		# fetch and loop through the features
		pr.select( indexes, extent, True )

		f = QgsFeature()
		while pr.nextFeature( f ):
			# filter features by spatial filter
			if geom and not geom.intersects( f.geometry() ):
				continue

			# filter features by attribute values
			attrs = f.attributeMap()

			ok = True
			for index, val in attrs.iteritems():
				filterWdg = self.filterForField( fields[index].name() )
				if not filterWdg:
					continue

				if filterWdg.isActive() and not filterWdg.checkValue( val ):
					ok = False
					break

			if not ok:	# the feature was filtered out
				continue

			# append feature values to the lists
			x.append( attrs[ xIndex ] )
			if hasYField: y.append( attrs[ yIndex ] )


		if len(x) <= 0:
			QMessageBox.information(self, "Plot", "No features in the result")
			return

		from plotWidget import *
		if plotType == self.PLOT_HIST:
			dlg = HistogramPlotWdg(x, None, self.xAxisCombo.currentText(), "Frequency", self.titleEdit.text())
		elif plotType == self.PLOT_HIST_LOG:
			dlg = HistogramPlotWdg(x, None, self.xAxisCombo.currentText(), "log10(Frequency)", self.titleEdit.text(), {'yscale':'log'})
		elif plotType == self.PLOT_SCATTER:
			dlg = ScatterPlotWdg(x, y, self.xAxisCombo.currentText(), self.yAxisCombo.currentText(), self.titleEdit.text())
		else:
			return

		dlg.show()			

