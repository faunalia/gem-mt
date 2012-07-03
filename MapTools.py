# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Omero RT
Description          : Omero plugin map tools
Date                 : August 15, 2010 
copyright            : (C) 2010 by Giuseppe Sucameli (Faunalia)
email                : sucameli@faunalia.it
 ***************************************************************************/

Omero plugin
Works done from Faunalia (http://www.faunalia.it) with funding from Regione 
Toscana - S.I.T.A. (http://www.regione.toscana.it/territorio/cartografia/index.html)

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
import qgis.gui
import qgis.utils



class Drawer(qgis.gui.QgsMapToolEmitPoint):
	def __init__(self, canvas, isPolygon=False, props=None):
		self.canvas = canvas
		self.isPolygon = isPolygon
		self.props = props if props is not None else {}

		self.action = None
		self.isEmittingPoints = False

		qgis.gui.QgsMapToolEmitPoint.__init__(self, self.canvas)

		self.rubberBand = qgis.gui.QgsRubberBand( self.canvas, self.isPolygon )
		self.rubberBand.setColor( self.props.get('color', Qt.red) )
		self.rubberBand.setWidth( self.props.get('border', 1) )

		self.snapper = qgis.gui.QgsMapCanvasSnapper( self.canvas )

		QObject.connect(self.canvas, SIGNAL( "mapToolSet(QgsMapTool *)" ), self._toolChanged)

	def __del__(self):
		QObject.disconnect(self.canvas, SIGNAL( "mapToolSet(QgsMapTool *)" ), self._toolChanged)
		self.reset()
		del self.rubberBand
		del self.snapper
		self.deleteLater()


	def setAction(self, action):
		self.action = action

	def action(self):
		return self.action

	def setColor(self, color):
		self.rubberBand.setColor( color )


	def _toolChanged(self, tool):
		if self.action:
			self.action.setChecked( tool == self )

	def startCapture(self):
		self.canvas.setMapTool( self )

	def stopCapture(self):
		self._toolChanged( None )
		self.canvas.unsetMapTool( self )

	def reset(self):
		self.isEmittingPoints = False
		self.rubberBand.reset( self.isPolygon )

	def canvasPressEvent(self, e):
		if e.button() == Qt.RightButton:
			if self.isEmittingPoints:
				self.isEmittingPoints = False
				self.onEnd( self.geometry() )
			return

		if e.button() != Qt.LeftButton:
			return

		if not self.isEmittingPoints:	# first click
			self.reset()
		self.isEmittingPoints = True

		point = self.toMapCoordinates( e.pos() )
		self.rubberBand.addPoint( point, True )	# true to update canvas
		self.rubberBand.show()

	def canvasMoveEvent(self, e):
		if not self.isEmittingPoints:
			return

		if not self.props.get('enableSnap', True):
			point = self.toMapCoordinates( e.pos() )
		else:
			retval, snapResults = self.snapper.snapToBackgroundLayers( e.pos() )
			if retval == 0 and len(snapResults) > 0:
				point = snapResults[0].snappedVertex
			else:
				point = self.toMapCoordinates( e.pos() )

		self.rubberBand.movePoint( point )

	def canvasReleaseEvent(self, e):
		if not self.isEmittingPoints:
			return

		if self.isPolygon:
			return

		if self.props.get('mode', None) != 'segment':
			return

		self.isEmittingPoints = False
		self.onEnd( self.geometry() )


	def isValid(self):
		return self.rubberBand.numberOfVertices() > 0

	def geometry(self):
		if not self.isValid():
			return None
		geom = self.rubberBand.asGeometry()
		if geom == None:
			return
		return QgsGeometry( geom )	# return a new geometry

	def onEnd(self, geometry):
		self.stopCapture()
		if geometry == None:
			self.reset()
			return
		self.emit( SIGNAL( "geometryEmitted" ), geometry )

	def deactivate(self):
		qgis.gui.QgsMapTool.deactivate(self)

		if not self.props.get('keepAfterEnd', False):
			self.reset()

		self.emit(SIGNAL("deactivated()"))


class PolygonDrawer(Drawer):
	def __init__(self, canvas, props=None):
		Drawer.__init__(self, canvas, True, props)

class LineDrawer(Drawer):
	def __init__(self, canvas, props=None):
		Drawer.__init__(self, canvas, False, props)

class SegmentDrawer(Drawer):
	def __init__(self, canvas, props=None):
		props = props if isinstance(props, dict) else {}
		props['mode'] = 'segment'
		Drawer.__init__(self, canvas, False, props)


class FeatureFinder(qgis.gui.QgsMapToolEmitPoint):

	def __init__(self, canvas=None):
		qgis.gui.QgsMapToolEmitPoint.__init__(self, canvas=canvas)
		QObject.connect(self, SIGNAL( "canvasClicked(const QgsPoint &, Qt::MouseButton)" ), self.onEnd)

	def onEnd(self, point, button):
		self.stopCapture()
		self.emit( SIGNAL("pointEmitted"), point, button )

	@classmethod
	def findAtPoint(self, layer, point, onlyTheClosestOne=True, onlyIds=False):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

		# recupera il valore del raggio di ricerca
		settings = QSettings()
		(radius, ok) = settings.value( "/Map/identifyRadius", QGis.DEFAULT_IDENTIFY_RADIUS ).toDouble()
		if not ok or radius <= 0:
			radius = QGis.DEFAULT_IDENTIFY_RADIUS
		radius = MapTool.canvas.extent().width() * radius/100

		# crea il rettangolo da usare per la ricerca
		rect = QgsRectangle()
		rect.setXMinimum(point.x() - radius)
		rect.setXMaximum(point.x() + radius)
		rect.setYMinimum(point.y() - radius)
		rect.setYMaximum(point.y() + radius)
		rect = MapTool.canvas.mapRenderer().mapToLayerCoordinates(layer, rect)

		# recupera le feature che intersecano il rettangolo
		layer.select([], rect, True, True)

		ret = None

		if onlyTheClosestOne:
			minDist = -1
			featureId = None
			rect = QgsGeometry.fromRect(rect)
			count = 0

			f = QgsFeature()
			while layer.nextFeature(f):
				if onlyTheClosestOne:
					geom = f.geometry()
					distance = geom.distance(rect)
					if minDist < 0 or distance < minDist:
						minDist = distance
						featureId = f.id()

			if onlyIds:
				ret = featureId
			elif featureId != None:
				layer.featureAtId(featureId, f, True, True)
				ret = f

		else:
			IDs = []
			f = QgsFeature()
			while layer.nextFeature(f):
				IDs.append( f.id() )

			if onlyIds:
				ret = IDs
			else:
				ret = []
				for featureId in IDs:
					layer.featureAtId(featureId, f, True, True)
					ret.append( f )

		QApplication.restoreOverrideCursor()
		return ret

