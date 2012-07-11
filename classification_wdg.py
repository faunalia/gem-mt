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

class ClassificationDock(QDockWidget):
	def __init__(self, iface, vl, parent=None):
		QDockWidget.__init__(self, parent)

		self.mainWidget = ClassificationWdg(iface, vl, self)
		self.setupUi()

	def deleteLater(self, *args):
		self.mainWidget.deleteLater()
		return QDockWidget.deleteLater(self, *args)

	def closeEvent(self, event):
		self.mainWidget.onClosing()
		self.emit( SIGNAL( "closed" ), self )
		return QDockWidget.closeEvent(self, event)

	def setupUi(self):
		self.setWindowTitle( "Classification panel" )
		self.setObjectName( "gem_mt_classification_dockwidget" )
		self.setWidget( self.mainWidget )


from ui.classificationWdg_ui import Ui_ClassificationWdg
from MapTools import PolygonDrawer, SegmentDrawer

class ClassificationWdg(QWidget, Ui_ClassificationWdg):

	def __init__(self, iface, vl, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi(self)

		# store the passed vars
		self.iface = iface
		self.vl = vl

		self.canvas = self.iface.mapCanvas()
		self._prevMapTool = None
		self._sharedData = {}	# it will contain the classification map (data shared through the all cross sections)

		# create the maptool to define the area of interest
		self.areaDrawer = PolygonDrawer(self.iface.mapCanvas(), {'color':QColor('black'), 'border':2, 'enableSnap':False, 'keepAfterEnd':True})
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

	def onClosing(self):
		self.showRubberBands(False)
		self.restorePrevMapTool()


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
			data = model.data( model.index(row, 0), Qt.UserRole ).toPyObject()
			segment, (midlineRb, bufferRb), dlg = data

			midlineRb.show() if show else midlineRb.hide()
			bufferRb.show() if show else bufferRb.hide()
			if dlg: dlg.hide()


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
		if self.canvas.mapUnits() == QGis.Meters:
			bufferwidth = 100
		elif self.canvas.mapUnits() == QGis.Feet:
			bufferwidth = 300
		else:
			bufferwidth = 1.0

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
		data = model.data( model.index(row, 0), Qt.UserRole ).toPyObject()
		segment, (midlineRb, bufferRb), dlg = data

		# delete the item
		model.removeRows( row, 1 )

		# destroy item data
		midlineRb.reset(False)
		bufferRb.reset(True)
		if dlg:
			dlg.close()
			dlg.deleteLater()

	def updateBuffer(self, index):
		""" re-draw the rubberbands for the classification buffer at index """
		model = self.buffersTable.model()

		buffersize = model.data( model.index(index.row(), 0) ).toDouble()[0]
		data = model.data( model.index(index.row(), 0), Qt.UserRole ).toPyObject()
		segment, (midlineRb, bufferRb), dlg = data

		self.redrawBufferRubberBand(bufferRb, segment, buffersize)
		self.redrawMidlineRubberBand(midlineRb, segment)


	def buffersSelectionChanged(self, current, previous):
		""" update buttons, then highlight the rubberbands for the 
			selected classification buffer """
		self.delBufferBtn.setEnabled(current.isValid())
		self.crossSectionBtn.setEnabled(current.isValid())

		model = self.buffersTable.model()
		for index in (previous, current):
			if not index.isValid():
				continue

			buffersize = model.data( model.index(index.row(), 0) ).toDouble()[0]
			data = model.data( model.index(index.row(), 0), Qt.UserRole ).toPyObject()
			segment, (midlineRb, bufferRb), dlg = data

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
		data = model.data( model.index(index.row(), 0), Qt.UserRole ).toPyObject()
		segment, (midlineRb, bufferRb), dlg = data

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
		from settings_dlg import Settings
		key2index = Settings.key2indexFieldMap( pr.fields() )
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
			x.append( midlineGeom.distance( geom ) )
			y.append( f.attributeMap()[ depthIndex ].toDouble()[0] * -1 )
			info.append( f.id() )

		if len(x) <= 0:
			QMessageBox.information(self, "Cross section", "No features in the result")
			return

		# plot now!
		if not dlg:
			from plot_wdg import CrossSectionDlg
			dlg = CrossSectionDlg(self._sharedData, self)

			# store the dialog into the item data
			data[2] = dlg
			model.setData( model.index(index.row(), 0), QVariant(data), Qt.UserRole )

		dlg.setData(x, y, info)
		dlg.setLabels( "Distance", "Depth" )

		self.updateClassification()
		dlg.show()

	def updateClassification(self):
		model = self.buffersTable.model()

		# update the earthquakes classification
		self._sharedData.clear()

		for row in range(model.rowCount()):
			dlg = model.data( model.index(row, 0), Qt.UserRole ).toPyObject()[2]
			if dlg == None:
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


			dlg.setDirty(True)


	def loadClassifiedData(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

		# store the current render flag state, then unset it
		prev_render_flag = self.iface.mapCanvas().renderFlag()
		self.iface.mapCanvas().setRenderFlag( False )
		try:
			self._loadClassifiedData()
		finally:
			# restore the render flag state
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

		inpr = self.vl.dataProvider()

		# create the output layer
		def memoryTypeName(fld):
			if fld.type() == QVariant.Int:
				return "integer"
			elif fld.type() == QVariant.Double:
				return "double"
			return "string"

		uri = u"Point?crs=epsg:4326&field=classType:string"
		for index, field in sorted(inpr.fields().iteritems()):
			uri += u"&field=%s:%s" % (field.name(), memoryTypeName(field))

		outvl = QgsVectorLayer(uri, "classified", "memory")
		outvl.startEditing()

		# fetch and loop through the features
		inpr.select(self.vl.pendingAllAttributesList(), areaGeom.boundingBox(), True)

		toMapCrsTransform = QgsCoordinateTransform( self.vl.crs(), self.canvas.mapRenderer().destinationCrs() )
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

			# transform to map CRS
			if geom.transform( toMapCrsTransform ) != 0:
				continue
			geom = QgsGeometry.fromPoint(geom.asPoint())

			# add the feature
			attrs = { 0 : 'shallow' if classType == 0 else 'deep' }
			for index, attr in sorted(f.attributeMap().iteritems()):
				attrs[ len(attrs) ] = attr
			f.setAttributeMap( attrs )
			outvl.addFeature( f )

		if not outvl.commitChanges():
			QMessageBox.warning( self, "Error", outvl.commitErrors().join("\n") )
			outvl.deleteLater()
			return

		# update layer's extent when new features have been added
		# because change of extent in provider is not propagated to the layer
		outvl.updateExtents()

		# set a categorized style
		from qgis.core import QgsSymbolV2, QgsCategorizedSymbolRendererV2, QgsRendererCategoryV2
		# create a category for each class
		categories = []

		# shallow earthquakes in red
		symbol = QgsSymbolV2.defaultSymbol( QGis.Point )
		symbol.setColor( QColor( "red" ) )
		cat = QgsRendererCategoryV2( "shallow", symbol, "shallow" )
		categories.append( cat )

		# deep earthquakes in blue
		symbol = QgsSymbolV2.defaultSymbol( QGis.Point )
		symbol.setColor( QColor( "blue" ) )
		cat = QgsRendererCategoryV2( "deep", symbol, "deep" )
		categories.append( cat )

		# create and set the renderer for the layer
		renderer = QgsCategorizedSymbolRendererV2( "classType", categories )
		outvl.setRendererV2( renderer )

		# add the layer to the map
		if hasattr(QgsMapLayerRegistry.instance(), 'addMapLayers'):	# available from QGis >= 1.8
			QgsMapLayerRegistry.instance().addMapLayers( [ outvl ] )
		else:
			QgsMapLayerRegistry.instance().addMapLayer( outvl )


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
			item = QStandardItem(unicode( buffersize ))
			item.setFlags( item.flags() | Qt.ItemIsEditable )

			self.appendRow( [item] )

			# store the rubberbands as user data
			row = self.rowCount()-1
			self.setData(self.index(row, 0), QVariant(data), Qt.UserRole)
			return row

		def setData(self, index, data, role=Qt.EditRole):
			ret = QStandardItemModel.setData(self, index, data, role)
			if role == Qt.EditRole and index.column() == 0:
				self.emit( SIGNAL("bufferWidthChanged"), index )
			return ret

