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

	def closeEvent(self, event):
		self.mainWidget.clear()

		self.emit( SIGNAL( "closed" ), self )
		return QDockWidget.closeEvent(self, event)

	def deleteLater(self):
		self.mainWidget.deleteLater()
		return QDockWidget.deleteLater(self)

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
		self.connect( self.buffersTable.model(), SIGNAL("rubberBandsUpdateRequested"), self.updateBuffer)

		# connect actions to the widgets
		self.connect(self.drawAreaBtn, SIGNAL("clicked()"), self.drawArea)
		self.connect(self.clearAreaBtn, SIGNAL("clicked()"), self.clearArea)
		self.connect(self.addBufferBtn, SIGNAL("clicked()"), self.drawBuffer)
		self.connect(self.delBufferBtn, SIGNAL("clicked()"), self.deleteBuffer)


	def storePrevMapTool(self):
		prevMapTool = self.canvas.mapTool()
		if prevMapTool not in (self.areaDrawer, self.segmentDrawer):
			self._prevMapTool = prevMapTool

	def restorePrevMapTool(self):
		if self._prevMapTool: 
			self.canvas.setMapTool(self._prevMapTool)


	def clear(self):
		self.clearArea()
		self.clearBuffers()

	def deleteLater(self):
		# restore the previous maptool
		self.areaDrawer.stopCapture()
		self.restorePrevMapTool()

		# delete the polygon drawer maptool
		self.areaDrawer.reset()
		self.areaDrawer.deleteLater()
		self.areaDrawer = None

		return QWidget.deleteLater(self)


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
		self.areaDrawer.stopCapture()
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
		self.segmentDrawer.stopCapture()
		self.restorePrevMapTool()

		if not line:
			return

		#TODO: reproject line to layer CRS
		#line = ...
		segment = line.asPolyline()

		#TODO: define buffer width in layer CRS unit
		bufferwidth = 10

		# create the midline rubber band
		midlineRb = QgsRubberBand(self.canvas, False)
		midlineRb.setColor( QColor('cyan') )
		midlineRb.setWidth( 3 )

		# create the buffer rubber band
		bufferRb = QgsRubberBand(self.canvas, True)
		bufferRb.setColor( QColor('fuchsia') )
		bufferRb.setWidth( 1 )

		# draw the buffer midline and area
		self.redrawBufferRubberBand( bufferRb, segment, bufferwidth )
		self.redrawMidlineRubberBand( midlineRb, segment )

		row = self.buffersTable.model().append( bufferwidth, (midlineRb, bufferRb) )
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
		angle = math.atan((y2-y1)/(x2-x1)) if abs(x2-x1) >= 0.00001 else math.pi/2

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

		midlineRb, bufferRb = model.data( model.index(row, 0), Qt.UserRole ).toPyObject()
		model.removeRows( row, 1 )

		midlineRb.reset(False)
		bufferRb.reset(True)

	def updateBuffer(self, index):
		""" re-draw the rubberbands for the classification buffer at index """
		model = self.buffersTable.model()

		buffersize = model.data( model.index(index.row(), 0) ).toInt()[0]
		midlineRb, bufferRb = model.data( model.index(index.row(), 0), Qt.UserRole ).toPyObject()

		segment = QgsGeometry(midlineRb.asGeometry()).asPolyline()

		self.redrawBufferRubberBand(bufferRb, segment, buffersize)
		self.redrawMidlineRubberBand(midlineRb, segment)


	def buffersSelectionChanged(self, current, previous):
		""" highlight the rubberbands for the selected classification buffer """
		model = self.buffersTable.model()

		for index in (previous, current):
			if not index.isValid():
				continue

			buffersize = model.data( model.index(index.row(), 0) ).toInt()[0]
			midlineRb, bufferRb = model.data( model.index(index.row(), 0), Qt.UserRole ).toPyObject()

			segment = QgsGeometry(midlineRb.asGeometry()).asPolyline()

			midlineRb.setColor(QColor('#88FFFF')) if index == current else midlineRb.setColor(QColor('#00FFFF'))	# color cyan
			bufferRb.setColor(QColor('#FF88FF')) if index == current else bufferRb.setColor(QColor('#FF00FF'))	# color fuchsia

			self.redrawBufferRubberBand(bufferRb, segment, buffersize)
			self.redrawMidlineRubberBand(midlineRb, segment)


	class BuffersTableModel(QStandardItemModel):
		def __init__(self, parent=None):
			self.header = ["Buffer size"]
			QStandardItemModel.__init__(self, 0, len(self.header), parent)

		def headerData(self, section, orientation, role):
			if role == Qt.DisplayRole:
				if orientation == Qt.Horizontal:
					return QVariant(self.header[section])
				if orientation == Qt.Vertical:
					return QVariant(section+1)
			return QVariant()

		def append(self, buffersize, rubberBands):
			item = QStandardItem(unicode( buffersize ))
			item.setFlags( item.flags() | Qt.ItemIsEditable )

			self.appendRow( [item] )

			# store the rubberbands as user data
			row = self.rowCount()-1
			self.setData(self.index(row, 0), QVariant(rubberBands), Qt.UserRole)
			return row

		def setData(self, index, data, role=Qt.EditRole):
			ret = QStandardItemModel.setData(self, index, data, role)
			if role == Qt.EditRole and index.column() == 0:
				self.emit( SIGNAL("rubberBandsUpdateRequested"), index )
			return ret

