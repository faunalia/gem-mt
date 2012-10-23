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


	def deleteLater(self, *args):
		QObject.disconnect(self.canvas, SIGNAL( "mapToolSet(QgsMapTool *)" ), self._toolChanged)
		self.reset()
		self.canvas.scene().removeItem( self.rubberBand )	# delete the item (it is owned by the canvas)
		del self.rubberBand
		del self.snapper
		return qgis.gui.QgsMapToolEmitPoint.deleteLater(self, *args)


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
			prevIsEmittingPoints = self.isEmittingPoints
			self.isEmittingPoints = False
			if not self.isEmittingPoints:
				self.onEnd( self.geometry() )
			else:
				self.onEnd( None )
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
		return geom

	def onEnd(self, geometry):
		#self.stopCapture()
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

