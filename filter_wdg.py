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
import re
import traceback
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from utils import Utils
from MapTools import PolygonDrawer

from ui.filterWdg_ui import Ui_FilterWdg

class FilterWdg(QWidget, Ui_FilterWdg):

	PLOT_HIST, PLOT_HIST_LOG, PLOT_SCATTER = range(3)

	def __init__(self, iface, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi(self)

		# store the iface and the event layer
		self.iface = iface
		self.vl = Utils.eventsVl()

		self.canvas = self.iface.mapCanvas()
		self._prevMapTool = None

		# setup the magnitude, depth and range filters
		self.setupFilters()

		# create the maptool to draw polygons
		self.polygonDrawer = PolygonDrawer( self.canvas, {'color':QColor(102,102,102, 90), 'enableSnap':False, 'keepAfterEnd':True} )
		self.polygonDrawer.setAction( self.drawPolygonBtn )
		self.connect(self.polygonDrawer, SIGNAL("geometryEmitted"), self.polygonCreated)

		# populate plot type combo
		self.plotTypeCombo.addItem( "Histogram", self.PLOT_HIST )
		self.plotTypeCombo.addItem( "Histogram (log10)", self.PLOT_HIST_LOG )
		self.plotTypeCombo.addItem( "Scatter plot", self.PLOT_SCATTER )
		self.updateAxesCombos()

		# populate both axis combos with field names
		fields = self.vl.dataProvider().fields()
		for index in range(fields.count()):
			self.xAxisCombo.addItem( fields[index].name(), index )
			self.yAxisCombo.addItem( fields[index].name(), index )

		# connect actions to the widgets
		self.connect(self.drawPolygonBtn, SIGNAL("clicked()"), self.drawPolygon)
		self.connect(self.clearPolygonBtn, SIGNAL("clicked()"), self.clearPolygon)
		self.connect(self.plotBtn, SIGNAL("clicked()"), self.createPlot)
		self.connect(self.plotTypeCombo, SIGNAL("currentIndexChanged(int)"), self.updateAxesCombos)


	def storePrevMapTool(self):
		prevMapTool = self.canvas.mapTool()
		if prevMapTool not in (self.polygonDrawer,):
			self._prevMapTool = prevMapTool

	def restorePrevMapTool(self):
		self.polygonDrawer.stopCapture()
		if self._prevMapTool: 
			self.canvas.setMapTool(self._prevMapTool)


	def showEvent(self, event):
		self.showRubberBands(True)
		QWidget.showEvent(self, event)

	def hideEvent(self, event):
		self.showRubberBands(False)
		self.restorePrevMapTool()
		QWidget.hideEvent(self, event)


	def deleteLater(self, *args):
		#print "deleting", self
		self.clearPolygon()

		# restore the previous maptool
		self.restorePrevMapTool()

		# delete the polygon drawer maptool
		self.polygonDrawer.deleteLater()
		self.polygonDrawer = None

		QWidget.deleteLater(self, *args)


	def _filterForKey(self, key):
		if key == None: return None
		if 'magnitude' in key: return self.magnitudeRangeFilter
		if 'depth' in key: return self.depthRangeFilter
		if 'date' in key: return self.dateRangeFilter
		return None

	def _hasPlotYField(self, plotType):
		return plotType not in (self.PLOT_HIST, self.PLOT_HIST_LOG)

	def _getPlotType(self):
		return self.plotTypeCombo.itemData( self.plotTypeCombo.currentIndex() )

	def updateAxesCombos(self):
		self.yAxisCombo.setEnabled( self._hasPlotYField( self._getPlotType() ) )


	def setupFilters(self):
		# setup the magnitude, depth and range filters
		self.magnitudeRangeFilter.setEnabled(False)
		self.magnitudeRangeFilter.setOrientation( Qt.Horizontal )
		self.magnitudeRangeFilter.setDecimals( 1 )
		self.magnitudeRangeFilter.setMinimum( 0 )
		self.magnitudeRangeFilter.setMaximum( 10 )

		self.depthRangeFilter.setEnabled(False)
		self.depthRangeFilter.setOrientation( Qt.Horizontal )
		self.depthRangeFilter.setMinimum( 0 )
		self.depthRangeFilter.setMaximum( 1000 )

		self.dateRangeFilter.setEnabled(False)
		self.dateRangeFilter.setOrientation( Qt.Horizontal )

		# take min/max values index from the data provider,
		# buf first let's reset the subset string to get real min/max
		pr = self.vl.dataProvider()
		pr.setSubsetString("")

		key2index = Utils.key2indexFieldMap( pr.fields() )
		for key, index in key2index.iteritems():
			filterWdg = self._filterForKey( key )
			if not filterWdg:
				continue

			minVal = pr.minimumValue( index )
			maxVal = pr.maximumValue( index )
			if minVal != None and maxVal != None:
				# check for empty strings (the provider could be unable to retrieve values)
				if minVal is None or maxVal is None:
					# let's search the real min/max values
					request = QgsFeatureRequest()
					request.setSubsetOfAttributes([index])
					for f in self.vl.getFeatures( request ):
						fval = Utils.valueFromQVariant( f.attributes()[index] )
						if not minVal or fval < minVal:
							minVal = fval
						if not maxVal or fval > maxVal:
							maxVal = fval
				else:
					minVal = Utils.valueFromQVariant( minVal )
					maxVal = Utils.valueFromQVariant( maxVal )

				# setup filter min/max range
				try:
					filterWdg.setMinimum( minVal )
					filterWdg.setLowValue( minVal )
					filterWdg.setMaximum( maxVal )
					filterWdg.setHighValue( maxVal )
				except Exception, ex:
					traceback.print_exc()
					#raise
					# unable to set min/max, skip the filter
					continue

				filterWdg.setEnabled(True)
				self.connect(filterWdg, SIGNAL("changeFinished"), self.updateMap)

		# filter default ranges
		self.magnitudeRangeFilter.setLowValue( 3.5 )
		self.magnitudeRangeFilter.setHighValue( 10 )
		self.depthRangeFilter.setLowValue( 0 )
		self.depthRangeFilter.setHighValue( 250 )

		self.updateMap()


	def updateMap(self, *args):
		pr = self.vl.dataProvider()
		key2index = Utils.key2indexFieldMap( pr.fields() )

		# convert filters to subset string
		subsets = []
		for key, index in key2index.iteritems():
			filterWdg = self._filterForKey( key )
			if not filterWdg or not filterWdg.isEnabled():
				continue

			name = pr.fields()[index].name()

			# define a new subset string when the low value is greather then the minimum value
			if filterWdg.lowValue() > filterWdg.minimum():
				minVal = filterWdg.lowValue()
				if type(minVal) in (QDate, QDateTime):
					dataFormat = "yyyy/MM/dd" if self.vl.providerType() == 'ogr' else "yyyy-MM-dd"
					minVal = u"'%s'" % minVal.toString(dataFormat)
				else:
					minVal = str(minVal)
				subsets.append( u"\"%s\" >= %s" % (re.sub('"', '""', name), minVal) )

			# define a new subset string when the high value is less then the maximum value
			if filterWdg.highValue() < filterWdg.maximum():
				maxVal = filterWdg.highValue()
				if type(maxVal) in (QDate, QDateTime):
					dataFormat = "yyyy/MM/dd" if self.vl.providerType() == 'ogr' else "yyyy-MM-dd"
					maxVal = u"'%s'" % maxVal.toString(dataFormat)
				else:
					maxVal = str(maxVal)
				subsets.append( u"\"%s\" <= %s" % (re.sub('"', '""', name), maxVal) )

		# set the subset string, then update the layer
		if self.vl.setSubsetString( u" AND ".join(subsets) ):
			self.vl.triggerRepaint()


	def showRubberBands(self, show=True):
		""" show/hide all the rubberbands """
		if self.polygonDrawer.isEmittingPoints:
			self.polygonDrawer.reset()
		else:
			self.polygonDrawer.rubberBand.show() if show else self.polygonDrawer.rubberBand.hide()

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
		self.restorePrevMapTool()


	def createPlot(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			dlg = self._createPlotDlg()
		finally:
			QApplication.restoreOverrideCursor()

		if dlg:
			dlg.show()
			dlg.exec_()
			dlg.deleteLater()


	def _createPlotDlg(self):
		plotType = self._getPlotType()
		hasYField = self._hasPlotYField( plotType )

		# spatial filter
		spatialFilter = self.polygonDrawer.geometry()
		if not spatialFilter:
			extent = self.vl.extent()
		else:
			# convert the spatial filter to the layer CRS
			toLayerCrsTransform = QgsCoordinateTransform( self.canvas.mapRenderer().destinationCrs(), self.vl.crs() )
			ret = spatialFilter.transform( toLayerCrsTransform )
			if ret != 0:
				QMessageBox.warning(self, "Invalid area", "Unable to tranform the selected area to the layer CRS.")
				return
			extent = spatialFilter.boundingBox()

		# get the indexes of fields selected in the combos
		xIndex = int(self.xAxisCombo.itemData( self.xAxisCombo.currentIndex() ))
		yIndex = int(self.yAxisCombo.itemData( self.yAxisCombo.currentIndex() ))

		pr = self.vl.dataProvider()
		index2key = Utils.index2keyFieldMap( pr.fields() )

		indexes = []
		for fld in pr.fields().toList():
			index = pr.fields().indexFromName(fld.name())
			if index == xIndex:
				indexes.append( xIndex )
				continue

			if index == yIndex and hasYField:
				indexes.append( yIndex )
				continue
			
			filterWdg = self._filterForKey( Utils.fieldName2key( fld.name() ) )
			if filterWdg and filterWdg.isEnabled():
				indexes.append( index )


		# the following lists will contain x and y values
		x, y = ([], [])

		# fetch and loop through the features
		request = QgsFeatureRequest()
		request.setFilterRect( extent )
		request.setSubsetOfAttributes( indexes )
		for f in self.vl.getFeatures( request ):
			# filter features by spatial filter
			if spatialFilter and not spatialFilter.contains( f.geometry() ):
				continue

			# filter features by attribute values
			attrs = f.attributes()

			ok = True
			for index, val in enumerate(attrs):
				if not index2key.has_key( index ):
					continue	# unused field

				filterWdg = self._filterForKey( index2key[ index ] )
				if not filterWdg:
					continue	# the field has no associated filter widget

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

		from plot_wdg import HistogramPlotDlg, ScatterPlotDlg
		if plotType == self.PLOT_HIST:
			dlg = HistogramPlotDlg(None, [x], [self.xAxisCombo.currentText(), "Frequency"], self.titleEdit.text())
		elif plotType == self.PLOT_HIST_LOG:
			dlg = HistogramPlotDlg(None, [x], [self.xAxisCombo.currentText(), "Frequency"], self.titleEdit.text(), {'yscale':'log'})
		elif plotType == self.PLOT_SCATTER:
			dlg = ScatterPlotDlg(None, [x, y], [self.xAxisCombo.currentText(), self.yAxisCombo.currentText()], self.titleEdit.text())
		else:
			return

		return dlg

