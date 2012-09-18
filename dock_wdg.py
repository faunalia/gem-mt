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

from filter_wdg import FilterWdg
from classification_wdg import ClassificationWdg
from processing_wdg import ProcessingWdg

from utils import Utils

class GemMtDock(QDockWidget):
	def __init__(self, iface, parent=None):
		QDockWidget.__init__(self, parent)

		self.filterWdg = FilterWdg(iface, self)
		self.classificationWdg = ClassificationWdg(iface, self)
		self.processingWdg = ProcessingWdg(iface, self)

		self.setupUi()

	def deleteLater(self, *args):
		self.filterWdg.deleteLater()
		self.classificationWdg.deleteLater()
		self.processingWdg.deleteLater()
		self.stacked.deleteLater()
		return QDockWidget.deleteLater(self, *args)

	def closeEvent(self, event):
		self.emit( SIGNAL( "closed" ), self )
		return QDockWidget.closeEvent(self, event)

	def viewIndex(self):
		return self.stacked.currentIndex()

	def setViewIndex(self, index):
		old_index = self.viewIndex()
		if index == old_index:
			return

		self.stacked.setCurrentIndex(index)
		if index == 0:
			self.setWindowTitle( "Filter/Plot panel" )
		elif index == 1:
			self.setWindowTitle( "Classification panel" )
		elif index == 2:
			self.setWindowTitle( "Processing panel" )
		else:
			self.setWindowTitle( "GEM-MT panel" )

		# show/hide layers
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		prev_render_flag = Utils.iface.mapCanvas().renderFlag()
		Utils.iface.mapCanvas().setRenderFlag( False )
		try:
			if index in (1, 2):
				# add the layer with classified data
				Utils.addVectorLayer( Utils.classifiedVl() )
				# show or hide the events layer respectively when the classification or processing panel is shown
				Utils.iface.legendInterface().setLayerVisible( Utils.eventsVl(), index == 1 )
		finally:
			# restore render flag state and cursor
			Utils.iface.mapCanvas().setRenderFlag( prev_render_flag )
			QApplication.restoreOverrideCursor()


	def setupUi(self):
		self.setObjectName( "gem_mt_dockwidget" )
		self.setWindowTitle( "Filter/Plot panel" )

		self.stacked = QStackedWidget(self)
		self.stacked.addWidget( self.filterWdg )
		self.stacked.addWidget( self.classificationWdg )
		self.stacked.addWidget( self.processingWdg )
		self.setWidget( self.stacked )

		self.setViewIndex(0)

