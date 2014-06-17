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

from utils import Utils
from MapTools import PolygonDrawer

from ui.processingWdg_ui import Ui_ProcessingWdg

class ProcessingWdg(QWidget, Ui_ProcessingWdg):

	def __init__(self, iface, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi(self)

		# store the iface
		self.iface = iface

		self.canvas = self.iface.mapCanvas()
		self._prevMapTool = None

		self.algorithmStacked.setCurrentIndex(0)

		# create the maptool to draw polygons
		self.polygonDrawer = PolygonDrawer( self.canvas, {'color':QColor(102,102,102, 60), 'enableSnap':False, 'keepAfterEnd':True} )
		self.polygonDrawer.setAction( self.drawPolygonBtn )
		self.connect(self.polygonDrawer, SIGNAL("geometryEmitted"), self.polygonCreated)

		# connect actions to the widgets
		self.connect(self.drawPolygonBtn, SIGNAL("clicked()"), self.drawPolygon)
		self.connect(self.clearPolygonBtn, SIGNAL("clicked()"), self.clearPolygon)

		QObject.connect(self.declusterWdg, SIGNAL("dataRequested"), self.fillData)
		QObject.connect(self.completenessWdg, SIGNAL("dataRequested"), self.fillData)
		QObject.connect(self.recurrenceWdg, SIGNAL("dataRequested"), self.fillData)
		QObject.connect(self.maxMagnitudeWdg, SIGNAL("dataRequested"), self.fillData)


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

	def fillData(self, data, panMap):
		""" fetch data from the classified layer and put them into the 
			passed arguments:
			**data** list will contain the selected features attributes, 
			**panMap** dictionary will keep the association between fields and 
			 their position in the data list """

		classifiedVl = Utils.classifiedVl()
		pr = classifiedVl.dataProvider()

		# spatial filter
		spatialFilter = self.polygonDrawer.geometry()
		if not spatialFilter:
			extent = QgsRectangle()
		else:
			# convert the spatial filter to the layer CRS
			toLayerCrsTransform = QgsCoordinateTransform( self.canvas.mapRenderer().destinationCrs(), classifiedVl.crs() )
			ret = spatialFilter.transform( toLayerCrsTransform )
			if ret != 0:
				QMessageBox.warning(self, "Invalid area", "Unable to tranform the selected area to the layer CRS.")
				return
			extent = spatialFilter.boundingBox()

		index2key = Utils.index2keyFieldMap( pr.fields() )

		# fetch and loop through the features
		request = QgsFeatureRequest()
		request.setFilterRect( extent )
		request.setSubsetOfAttributes( classifiedVl.pendingAllAttributesList() )
		for f in classifiedVl.getFeatures( request ):
			# filter features by spatial filter
			if spatialFilter and not spatialFilter.contains( f.geometry() ):
				continue

			# create a new row: [id, *fields]
			attrs = f.attributes()
			row = [ f.id() ]
			for index, val in enumerate( attrs ):
				row.append( val )

				# store the index of well-known field in the pan map so they
				# can be found easily later
				key = index2key.get(index, None)
				if key is not None:
					panMap[key] = len(row)-1

			# append to the data buffer
			data.append( row )

		if len(data) <= 0:
			QMessageBox.information(self, "Processing", "No features in the result")
			return

