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

from MapTools import PolygonDrawer, SegmentDrawer
from utils import Utils, LayerStyler

from ui.classificationWdg_ui import Ui_ClassificationWdg

class ClassificationWdg(QWidget, Ui_ClassificationWdg):

	def __init__(self, iface, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi(self)

		# store the iface and the events layer
		self.iface = iface
		self.vl = Utils.eventsVl()

		self.canvas = self.iface.mapCanvas()
		self._prevMapTool = None
		self._sharedData = {}	# it will contain the classification map (data shared through the all cross sections)

		# create the maptool to define the area of interest
		self.areaDrawer = PolygonDrawer(self.iface.mapCanvas(), {'color':QColor('#333333'), 'border':2, 'enableSnap':False, 'keepAfterEnd':True})
		self.areaDrawer.setAction( self.drawAreaBtn )
		self.connect(self.areaDrawer, SIGNAL("geometryEmitted"), self.areaCreated)

		# create the maptool to create classification buffers
		self.segmentDrawer = SegmentDrawer(self.iface.mapCanvas(), {'color':QColor('cyan'), 'border':3, 'enableSnap':False})
		self.segmentDrawer.setAction( self.addBufferBtn )
		self.connect(self.segmentDrawer, SIGNAL("geometryEmitted"), self.midlineBufferCreated)

		# initialize the table that will contain classification buffers
		self.buffersTable.setModel( self.BuffersTableModel(self.buffersTable) )
		self.connect( self.buffersTable.selectionModel(), SIGNAL("currentRowChanged(const QModelIndex &, const QModelIndex &)"), self.buffersSelectionChanged)
		self.connect( self.buffersTable.model(), SIGNAL("bufferWidthChanged"), self.updateBuffer)

		# connect actions to the widgets
		self.connect(self.drawAreaBtn, SIGNAL("clicked()"), self.drawArea)
		self.connect(self.clearAreaBtn, SIGNAL("clicked()"), self.clearArea)
		self.connect(self.addBufferBtn, SIGNAL("clicked()"), self.drawBuffer)
		self.connect(self.delBufferBtn, SIGNAL("clicked()"), self.deleteBuffer)
		self.connect(self.crossSectionBtn, SIGNAL("clicked()"), self.openCrossSection)
		self.connect(self.displayClassifiedDataBtn, SIGNAL("clicked()"), self.loadClassifiedData)

		# disable buttons
		self.delBufferBtn.setEnabled(False)
		self.crossSectionBtn.setEnabled(False)


	def storePrevMapTool(self):
		prevMapTool = self.canvas.mapTool()
		if prevMapTool and prevMapTool not in (self.areaDrawer, self.segmentDrawer):
			self._prevMapTool = prevMapTool

	def restorePrevMapTool(self):
		self.areaDrawer.stopCapture()
		self.segmentDrawer.stopCapture()
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
		# clear rubberbands
		self.clearArea()
		self.clearBuffers()

		# restore the previous maptool
		self.restorePrevMapTool()

		# delete the maptools
		self.areaDrawer.deleteLater()
		self.areaDrawer = None
		self.segmentDrawer.deleteLater()
		self.segmentDrawer = None

		return QWidget.deleteLater(self, *args)


	def showRubberBands(self, show=True):
		""" show/hide all the rubberbands """
		if self.areaDrawer.isEmittingPoints:
			self.areaDrawer.reset()
		else:
			self.areaDrawer.rubberBand.show() if show else self.areaDrawer.rubberBand.hide()
		self.segmentDrawer.reset()

		model = self.buffersTable.model()
		for row in range(model.rowCount()):
			# get item data
			index = model.index(row, 0)
			buffersize = model.getBufferSize(index)
			segment, (midlineRb, bufferRb), dlg = model.getAdditionalData(index)

			midlineRb.show() if show else midlineRb.hide()
			bufferRb.show() if show else bufferRb.hide()
			if dlg:
				dlg.hide()


	def drawArea(self):
		# store the previous maptool
		self.storePrevMapTool()

		# set the polygon drawer as current maptool
		self.areaDrawer.startCapture()

	def clearArea(self):
		# remove the displayed polygon
		self.areaDrawer.reset()

	def areaCreated(self, polygon):
		# restore the previous maptool
		self.restorePrevMapTool()
	

	def drawBuffer(self):
		""" set the maptool to draw the buffer midline """
		# store the previous maptool
		self.storePrevMapTool()

		# set the segment drawer as current maptool
		self.segmentDrawer.startCapture()


	def clearBuffers(self):
		""" delete all the classification buffers and related rubberbands """
		self.segmentDrawer.reset()

		model = self.buffersTable.model()
		for row in range(model.rowCount()-1, -1, -1):
			self.deleteBuffer(row)

		self.buffersTable.model().clear()


	def midlineBufferCreated(self, line):
		""" called after the buffer midline is drawn by the user """
		# restore the previous maptool
		self.restorePrevMapTool()

		# check for a valid segment
		if not line:
			return

		segment = line.asPolyline()
		if len(segment) != 2:
			return

		# create the midline rubber band
		midlineRb = QgsRubberBand(self.canvas, False)
		midlineRb.setColor( QColor('cyan') )
		midlineRb.setWidth( 3 )

		# create the buffer rubber band
		bufferRb = QgsRubberBand(self.canvas, True)
		bufferRb.setColor( QColor('fuchsia') )
		bufferRb.setWidth( 1 )

		# define buffer width in layer CRS unit
		units = self.canvas.mapUnits()
		if units == QGis.Meters:
			bufferwidth = 100000 # 100 Km
		elif units == QGis.Feet:
			bufferwidth = 300000 # 300 Kft
		else:
			bufferwidth = 1.0 # 1 degree

		# append the new classification buffer to the table
		data = [segment, (midlineRb, bufferRb), None]
		row = self.buffersTable.model().append( bufferwidth, data )
		self.buffersTable.setCurrentIndex( self.buffersTable.model().index( row, 0 ) )
		

	def redrawMidlineRubberBand(self, rubberBand, segment):
		""" re-draw the midline rubberband by segment """
		rubberBand.reset(False)

		# add points to the midline rubber band
		rubberBand.addPoint( segment[0], False )
		rubberBand.addPoint( segment[1], True )

		rubberBand.show()

	def redrawBufferRubberBand(self, rubberBand, segment, width):
		""" re-draw the buffer rubberband by segment and width """
		rubberBand.reset(True)

		# create a buffer around the line
		import math
		(x1,y1), (x2,y2) = segment
		angle = math.atan(float(y2-y1)/(x2-x1)) if x2-x1 != 0 else math.pi/2

		xincr, yincr = width*math.sin(angle), width*math.cos(angle)

		# add the buffer geom points to the rubber band
		rubberBand.addPoint( QgsPoint(x1+xincr, y1-yincr), False )
		rubberBand.addPoint( QgsPoint(x1-xincr, y1+yincr), False )
		rubberBand.addPoint( QgsPoint(x2-xincr, y2+yincr), False )
		rubberBand.addPoint( QgsPoint(x2+xincr, y2-yincr), True )

		rubberBand.show()


	def deleteBuffer(self, row=None):
		""" delete the classification buffer at row and its rubberbands """
		model = self.buffersTable.model()

		if row is None:
			row = self.buffersTable.currentIndex().row()

		if row < 0 or row >= model.rowCount():
			return

		# get item data
		segment, (midlineRb, bufferRb), dlg = model.getAdditionalData( model.index(row, 0) )

		# delete the item
		model.removeRows( row, 1 )

		# destroy item data
		midlineRb.reset(False)
		bufferRb.reset(True)
		if dlg:
			self.disconnect(self, SIGNAL("classificationUpdated"), dlg.refresh)
			dlg.close()
			dlg.deleteLater()

	def updateBuffer(self, index):
		""" re-draw the rubberbands for the classification buffer at index """
		model = self.buffersTable.model()

		buffersize = model.getBufferSize(index)
		segment, (midlineRb, bufferRb), dlg = model.getAdditionalData(index)

		self.redrawBufferRubberBand(bufferRb, segment, buffersize)
		self.redrawMidlineRubberBand(midlineRb, segment)

		if dlg:
			dlg.refresh()


	def buffersSelectionChanged(self, current, previous):
		""" update buttons, then highlight the rubberbands for the 
			selected classification buffer """
		self.delBufferBtn.setEnabled(current.isValid())
		self.crossSectionBtn.setEnabled(current.isValid())

		model = self.buffersTable.model()
		for index in (previous, current):
			if not index.isValid():
				continue

			buffersize = model.getBufferSize(index)
			segment, (midlineRb, bufferRb), dlg = model.getAdditionalData(index)

			midlineRb.setColor(QColor('#88FFFF')) if index == current else midlineRb.setColor(QColor('#00FFFF'))	# color cyan
			bufferRb.setColor(QColor('#FF88FF')) if index == current else bufferRb.setColor(QColor('#FF00FF'))	# color fuchsia

			self.redrawBufferRubberBand(bufferRb, segment, buffersize)
			self.redrawMidlineRubberBand(midlineRb, segment)


	def openCrossSection(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			dlg = self._openCrossSection()
		finally:
			QApplication.restoreOverrideCursor()

	def _openCrossSection(self):
		""" open a cross section displaying geometries within this 
			classification buffer """
		index = self.buffersTable.currentIndex()
		if not index.isValid():
			return

		# get the geometry which defines the area of interest
		areaGeom = self.areaDrawer.geometry()
		if not areaGeom or areaGeom.isGeosEmpty():
			QMessageBox.warning(self, "No Area of interest", "Define an Area of interest and then try again.")
			return

		# get midline and area geometries for the selected classification buffer
		model = self.buffersTable.model()
		segment, (midlineRb, bufferRb), dlg = model.getAdditionalData(index)

		midlineGeom = midlineRb.asGeometry()
		bufferGeom = bufferRb.asGeometry()

		# compute the spatial filter
		filteringGeom = bufferGeom.intersection( areaGeom )
		if not filteringGeom or filteringGeom.isGeosEmpty():
			QMessageBox.warning(self, "Invalid area", "Intersection between the Area of interest and the selected classification buffer area is invalid or empty.")
			return

		# convert the spatial filter to the layer CRS
		toLayerCrsTransform = QgsCoordinateTransform( self.canvas.mapRenderer().destinationCrs(), self.vl.crs() )
		ret = filteringGeom.transform( toLayerCrsTransform )
		if ret != 0:
			QMessageBox.warning(self, "Invalid area", "Unable to tranform the selected area to the layer CRS.")
			return

		# get the depth field index
		pr = self.vl.dataProvider()
		key2index = Utils.key2indexFieldMap( pr.fields() )
		depthIndex =  key2index['depth']

		# the following x and y lists will contain respectively the distance 
		# along the buffer and the depth, the info list instead will contain 
		# additional data
		x, y, info = [], [], []

		# fetch and loop through the features
		pr.select([ depthIndex ], filteringGeom.boundingBox(), True)

		toMapCrsTransform = QgsCoordinateTransform( self.vl.crs(), self.canvas.mapRenderer().destinationCrs() )
		f = QgsFeature()
		while pr.nextFeature( f ):
			geom = f.geometry()

			# filter features by spatial filter
			if not filteringGeom.contains( geom ):
				continue

			# transform to map CRS
			if geom.transform( toMapCrsTransform ) != 0:
				continue
			geom = QgsGeometry.fromPoint(geom.asPoint())

			# store distance and depth values
			dist = Utils.distanceAlongProfile( midlineGeom, geom )
			x.append( Utils.toDisplayedSize( dist )	)	# convert to Km/Kft/degrees
			y.append( f.attributeMap()[ depthIndex ].toDouble()[0] * -1 )
			info.append( f.id() )

		if len(x) <= 0:
			QMessageBox.information(self, "Cross section", "No features in the result")
			return

		# plot now!
		if not dlg:
			from cross_section_wdg import CrossSectionDlg
			dlg = CrossSectionDlg(self._sharedData, self)
			self.connect(dlg, SIGNAL("classificationUpdateRequested"), self.updateClassification)
			self.connect(self, SIGNAL("classificationUpdated"), dlg.refresh)

			# store the dialog into the item data
			model.setAdditionalData( index, [segment, (midlineRb, bufferRb), dlg] )

		dlg.setData(x, y, info)
		dlg.setLabels( "Distance", "Depth" )

		self.updateClassification()
		dlg.show()


	def updateClassification(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			self._updateClassification()
		finally:
			QApplication.restoreOverrideCursor()

	def _updateClassification(self):
		model = self.buffersTable.model()

		# update the earthquakes classification
		self._sharedData.clear()

		for row in range(model.rowCount()):
			
			dlg = model.getAdditionalData(model.index(row, 0))[2]
			if not dlg:
				continue

			classified = (shallow, deep) = dlg.classify()

			# update the shared data
			for typeIndex, data in enumerate( classified ):
				for fid in data:
					# avoid duplicates
					if self._sharedData.has_key(fid):
						# do not update shallow earthquakes
						if self._sharedData[ fid ] == 0:	
							continue	# already present

					self._sharedData[ fid ] = typeIndex

		self.emit( SIGNAL("classificationUpdated") )


	def loadClassifiedData(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

		# store the current render flag state, then unset it
		prev_render_flag = self.iface.mapCanvas().renderFlag()
		self.iface.mapCanvas().setRenderFlag( False )
		try:
			self._loadClassifiedData()
		finally:
			# restore render flag state and cursor
			self.iface.mapCanvas().setRenderFlag( prev_render_flag )
			QApplication.restoreOverrideCursor()

	def _loadClassifiedData(self):
		# get the geometry which defines the area of interest
		areaGeom = self.areaDrawer.geometry()
		if not areaGeom or areaGeom.isGeosEmpty():
			QMessageBox.warning(self, "No Area of interest", "Define an Area of interest and then try again.")
			return

		# convert the spatial filter to the layer CRS
		toLayerCrsTransform = QgsCoordinateTransform( self.canvas.mapRenderer().destinationCrs(), self.vl.crs() )
		ret = areaGeom.transform( toLayerCrsTransform )
		if ret != 0:
			QMessageBox.warning(self, "Invalid area", "Unable to tranform the selected area to the layer CRS.")
			return

		# update the classification
		self.updateClassification()

		classifiedVl = Utils.classifiedVl()
		outpr = classifiedVl.dataProvider()

		# remove all the features in the classified events layer
		classifiedVl.removeSelection()
		classifiedVl.invertSelection()
		outpr.deleteFeatures( classifiedVl.selectedFeaturesIds() )

		# fetch and loop through the features
		inpr = self.vl.dataProvider()
		inpr.select(self.vl.pendingAllAttributesList(), areaGeom.boundingBox(), True)

		betweenLayersCrsTransform = QgsCoordinateTransform( self.vl.crs(), classifiedVl.crs() )
		f = QgsFeature()
		while inpr.nextFeature( f ):
			geom = f.geometry()

			# filter features by spatial filter
			if not areaGeom.contains( geom ):
				continue

			# skip unclassified data
			if f.id() not in self._sharedData:
				continue
			classType = self._sharedData[ f.id() ]

			# transform to classified layer CRS
			if geom.transform( betweenLayersCrsTransform ) != 0:
				continue
			f.setGeometry( QgsGeometry.fromPoint(geom.asPoint()) )

			# set feature attributes
			attrs = {}
			for index, attr in sorted(f.attributeMap().iteritems()):
				attrs[ len(attrs) ] = attr
			attrs[ len(attrs) ] =  'shallow' if classType == 0 else 'deep'
			f.setAttributeMap( attrs )

			# add the feature
			outpr.addFeatures( [f] )

		# update layer's extent when new features have been added
		# because change of extent in provider is not propagated to the layer
		classifiedVl.updateExtents()

		# add the layer to the map
		Utils.addVectorLayer( classifiedVl )


	class BuffersTableModel(QStandardItemModel):
		def __init__(self, parent=None):
			self.header = ["Buffer width"]
			QStandardItemModel.__init__(self, 0, len(self.header), parent)

		def headerData(self, section, orientation, role):
			if role == Qt.DisplayRole:
				if orientation == Qt.Horizontal:
					return QVariant(self.header[section])
				if orientation == Qt.Vertical:
					return QVariant(section+1)
			return QVariant()

		def append(self, buffersize, data):
			item = QStandardItem()
			item.setFlags( item.flags() | Qt.ItemIsEditable )

			self.appendRow( [item] )
			row = self.rowCount()-1

			# store buffersize and additional data
			self.blockSignals(True)
			self.setBufferSize(self.index(row, 0), buffersize)
			self.setAdditionalData(self.index(row, 0), data)
			self.blockSignals(False)

			# a new buffer was added, trigger for its repainting
			self.emit( SIGNAL("bufferWidthChanged"), self.index(row, 0) )

			return row

		def setData(self, index, data, role=Qt.EditRole):
			ret = QStandardItemModel.setData(self, index, data, role)
			if role == Qt.EditRole and index.column() == 0:
				self.emit( SIGNAL("bufferWidthChanged"), index )
			return ret


		def getBufferSize(self, index):
			if index.isValid():
				displayed_size = self.data( self.index(index.row(), 0) ).toDouble()[0]
				# convert back to m/ft/degrees
				return Utils.fromDisplayedSize( displayed_size )

		def setBufferSize(self, index, buffersize):
			if index.isValid():
				# display Km/Kft/degrees
				displayed_size = Utils.toDisplayedSize( buffersize )
				self.setData( self.index(index.row(), 0), QVariant( displayed_size ) )

		def getAdditionalData(self, index):
			if index.isValid():
				return self.data( self.index(index.row(), 0), Qt.UserRole ).toPyObject()

		def setAdditionalData(self, index, data):
			if index.isValid():
				self.setData( self.index(index.row(), 0), QVariant(data), Qt.UserRole )

