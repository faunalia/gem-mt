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

from qgis.core import QGis, QgsVectorLayer, QgsField, QgsMapLayerRegistry
from utils import Utils, LayerStyler

import resources_rc

class GEM_MT_Plugin:

	instance = None

	def __init__(self, iface):
		GEM_MT_Plugin.instance = self

		self.iface = iface
		self.toolbar = None
		self.dock = None

		self.vl = None
		self.basemapVl = None
		self.classifiedVl = None

	def initGui(self):
		# create the actions
		self.loadCsvAction = QAction( QIcon( ":/gem-mt_plugin/icons/csv" ), "Load CSV file", self.iface.mainWindow() )
		QObject.connect( self.loadCsvAction, SIGNAL( "triggered()" ), self.loadCsv )

		self.useActiveLayerAction = QAction( QIcon( ":/gem-mt_plugin/icons/active_layer" ), "Use active layer", self.iface.mainWindow() )
		QObject.connect( self.useActiveLayerAction, SIGNAL( "triggered()" ), self.useActiveLayer )

		self.plotStatsAction = QAction( QIcon( ":/gem-mt_plugin/icons/stats" ), "Plot statistics", self.iface.mainWindow() )
		self.plotStatsAction.setCheckable(True)
		QObject.connect( self.plotStatsAction, SIGNAL( "triggered()" ), self.displayFilterPanel )

		self.classificationAction = QAction( QIcon( ":/gem-mt_plugin/icons/classification" ), "Classification", self.iface.mainWindow() )
		self.classificationAction.setCheckable(True)
		QObject.connect( self.classificationAction, SIGNAL( "triggered()" ), self.displayClassificationPanel )

		self.routinesAction = QAction( QIcon( ":/gem-mt_plugin/icons/processing" ), "Processing", self.iface.mainWindow() )
		self.routinesAction.setCheckable(True)
		QObject.connect( self.routinesAction, SIGNAL( "triggered()" ), self.displayRoutinesPanel )


		self.settingsAction = QAction( QIcon( ":/gem-mt_plugin/icons/settings" ), "Settings", self.iface.mainWindow() )
		QObject.connect( self.settingsAction, SIGNAL( "triggered()" ), self.settings )

		self.aboutAction = QAction( QIcon( ":/gem-mt_plugin/icons/about" ), "About", self.iface.mainWindow() )
		QObject.connect( self.aboutAction, SIGNAL("triggered()"), self.about )

		# create a custom toolbar
		self.toolbar = self.iface.addToolBar( "GEM-MT Plugin" )

		# add actions to toolbars and menus
		self.toolbar.addAction( self.loadCsvAction )
		self.toolbar.addAction( self.useActiveLayerAction )
		self.toolbar.addAction( self.plotStatsAction )
		self.toolbar.addAction( self.classificationAction )
		self.toolbar.addAction( self.routinesAction )
		self.iface.addPluginToMenu( "&EQCAP Plugin", self.loadCsvAction )
		self.iface.addPluginToMenu( "&EQCAP Plugin", self.useActiveLayerAction )
		self.iface.addPluginToMenu( "&EQCAP Plugin", self.plotStatsAction )
		self.iface.addPluginToMenu( "&EQCAP Plugin", self.classificationAction )
		self.iface.addPluginToMenu( "&EQCAP Plugin", self.routinesAction )
		self.iface.addPluginToMenu( "&EQCAP Plugin", self.settingsAction )
		self.iface.addPluginToMenu( "&EQCAP Plugin", self.aboutAction )

	def unload(self):
		# delete the dockwidget
		self.destroyDock()

		# cleanup stuff related to the loaded layers
		if self.vl:
			QObject.disconnect( self.vl, SIGNAL("layerDeleted()"), self.layerDestroyed )
			self.vl = None

		if self.basemapVl:
			QObject.disconnect( self.basemapVl, SIGNAL("layerDeleted()"), self.basemapLayerDestroyed )
			self.basemapVl = None

		if self.classifiedVl:
			QObject.disconnect( self.classifiedVl, SIGNAL("layerDeleted()"), self.classifiedLayerDestroyed )
			self.classifiedVl = None

		# remove actions from toolbars and menus
		self.toolbar.removeAction( self.loadCsvAction )
		self.toolbar.removeAction( self.useActiveLayerAction )
		self.toolbar.removeAction( self.plotStatsAction )
		self.toolbar.removeAction( self.classificationAction )
		self.toolbar.removeAction( self.routinesAction )
		self.iface.removePluginMenu( "&EQCAP Plugin", self.loadCsvAction )
		self.iface.removePluginMenu( "&EQCAP Plugin", self.useActiveLayerAction )
		self.iface.removePluginMenu( "&EQCAP Plugin", self.plotStatsAction )
		self.iface.removePluginMenu( "&EQCAP Plugin", self.classificationAction )
		self.iface.removePluginMenu( "&EQCAP Plugin", self.routinesAction )
		self.iface.removePluginMenu( "&EQCAP Plugin", self.settingsAction )
		self.iface.removePluginMenu( "&EQCAP Plugin", self.aboutAction )

		# delete the custom toolbar
		self.toolbar.deleteLater()
		self.toolbar = None

		GEM_MT_Plugin.instance = None


	def about(self):
		""" display the about dialog """
		from about_dlg import AboutDlg
		dlg = AboutDlg( self.iface.mainWindow() )
		dlg.exec_()

	def settings(self):
		""" display the about dialog """
		from .settings_dlg import SettingsDlg
		dlg = SettingsDlg( self.iface.mainWindow() )
		dlg.exec_()
		

	def loadCsv(self):
		""" load the CSV file selected by the user """
		# ask for the csv file
		filename = QFileDialog.getOpenFileName(self.iface.mainWindow(), "Select a csv file", "", "CSV file (*.csv)")
		if not filename:
			return
		if filename and filename == "":
			return	# cancel clicked

		
		# unset the render flag
		prev_render_flag = self.iface.mapCanvas().renderFlag()
		self.iface.mapCanvas().setRenderFlag( False )

		# set the waiting cursor
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			# import CSV file to SL database
			from importer import CsvToSL
			importer = CsvToSL(filename, self.iface.mainWindow())
			retCode, vl = importer.run()
			
			importer.deleteLater()
			del importer

			# ret code check
			if vl is None or retCode != CsvToSL.OK:
				if retCode == CsvToSL.INVALID_LATLON:
					self.settings()	# show the settings dialog
				return
			
			# ok, the new layer can be used with the plugin
			# remove the previous loaded layer, then store the new one
			self.removeLayer()
			self.setLayer(vl)

			# add the basemap layer, then the new layer
			self.addBasemapLayer()
			Utils.addVectorLayer(self.vl)
			
		finally:
			# restore the cursor and render flag state
			QApplication.restoreOverrideCursor()
			self.iface.mapCanvas().setRenderFlag( prev_render_flag )
			# zomm to extent
			self.iface.mapCanvas().setExtent(self.basemapVl.extent())

	def basemapLayer(self):
		return self.basemapVl

	def addBasemapLayer(self):
		if self.basemapVl:
			return # already added

		current_dir = QFileInfo(__file__).absoluteDir()
		basemap = current_dir.absoluteFilePath( u"data/basemap/Countries.shp" )

		# load the basemap layer
		vl = QgsVectorLayer(basemap, QFileInfo(basemap).baseName(), "ogr")
		if not vl.isValid():
			vl.deleteLater()
			return

		# add the basemap layer to canvas
		LayerStyler.setBasemapStyle(vl)
		self.basemapVl = vl
		QObject.connect( self.basemapVl, SIGNAL("layerDeleted()"), self.basemapLayerDestroyed )
		Utils.addVectorLayer(vl)

	def basemapLayerDestroyed(self):
		self.basemapVl = None


	def eventsLayer(self):
		return self.vl

	def useActiveLayer(self):
		vl = self.iface.activeLayer()
		if not vl:
			QMessageBox.warning( self.iface.mainWindow(), "Invalid layer", u"No point layer selected." )
			return

		if vl.geometryType() != QGis.Point:
			QMessageBox.warning( self.iface.mainWindow(), "Invalid layer", u"The selected layer is not a Point layer." )
			return

		# store the current render flag state, then unset it
		prev_render_flag = self.iface.mapCanvas().renderFlag()
		self.iface.mapCanvas().setRenderFlag( False )

		# set the waiting cursor
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			# remove the previous loaded layer, then store the new one
			self.removeLayer()
			self.setLayer(vl)
			# add the base map
			self.addBasemapLayer()
		finally:
			# restore cursor and render flag state
			QApplication.restoreOverrideCursor()
			self.iface.mapCanvas().setRenderFlag( prev_render_flag )


	def setLayer(self, vl):
		""" set the layer as the current one used by the plugin """
		# store the new layer
		LayerStyler.setEarthquakesStyle(vl)
		self.vl = vl
		self.vl.layerDeleted.connect( self.layerDestroyed )

		# create the layer that will contain classified point
		self.createClassifiedLayer()

		# enable the filter/plot panel
		self.createDock()
		self.updateActionsState()

	def removeLayer(self):
		if self.vl:
			# destroy the docked panel
			self.destroyDock()

			self.vl.layerDeleted.connect( self.layerDestroyed )
			QgsMapLayerRegistry.instance().removeMapLayer( self.vl.id() )
			self.vl = None

	def layerDestroyed(self):
		self.destroyDock()
		self.vl = None


	def classifiedLayer(self):
		if not self.classifiedVl:
			# (re)create the layer if needed
			self.createClassifiedLayer()
		return self.classifiedVl

	def createClassifiedLayer(self):
		if not self.vl:
			return

		self.removeClassifiedLayer()

		# create the output layer
		classField = "classType"

		fields = map( lambda x: x, self.vl.dataProvider().fields().toList() )
		fields += [ QgsField(classField, QVariant.String) ]

		vl = Utils.createMemoryLayer( 'Point', self.vl.crs().authid(), fields, "classified" )
		if not vl:
			return

		# set style
		LayerStyler.setClassifiedStyle( vl, classField, 0.8 )

		self.classifiedVl = vl
		QObject.connect( self.classifiedVl, SIGNAL("layerDeleted()"), self.classifiedLayerDestroyed )

	def removeClassifiedLayer(self):
		if self.classifiedVl:
			QObject.disconnect( self.classifiedVl, SIGNAL("layerDeleted()"), self.classifiedLayerDestroyed )
			#QgsMapLayerRegistry.instance().removeMapLayer( self.classifiedVl.id() )
			self.classifiedVl = None

	def classifiedLayerDestroyed(self):
		self.classifiedVl = None


	def createDock(self):
		if not self.dock:
			from dock_wdg import GemMtDock
			self.dock = GemMtDock( self.iface )
			QObject.connect(self.dock, SIGNAL("closed"), self.onDockClosed)
			self.updateDockView()

		if not self.dock.isVisible():
			self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

	def updateDockView(self):
		if self.plotStatsAction.isChecked():
			self.dock.setViewIndex(0)
		elif self.classificationAction.isChecked():
			self.dock.setViewIndex(1)
		elif self.routinesAction.isChecked():
			self.dock.setViewIndex(2)
		else:
			self.dock.close()

	def onDockClosed(self):
		self.resetActionsState()

	def destroyDock(self):
		if self.dock:
			self.dock.close()
			self.dock.deleteLater()
			self.dock = None


	def resetActionsState(self):
		self.plotStatsAction.setChecked(False)
		self.classificationAction.setChecked(False)
		self.routinesAction.setChecked(False)

	def updateActionsState(self):
		index = self.dock.viewIndex()
		self.plotStatsAction.setChecked(index == 0)
		self.classificationAction.setChecked(index == 1)
		self.routinesAction.setChecked(index == 2)


	def displayClassificationPanel(self):
		if not self.classificationAction.isChecked():
			self.updateDockView()
			return

		if not self.vl:
			QMessageBox.warning( self.iface.mainWindow(), "No layer loaded", u"Load a CSV layer and then try again." )
			self.classificationAction.setChecked(False)
			return

		self.resetActionsState()
		self.classificationAction.setChecked(True)

		self.createDock()
		self.updateDockView()

	def displayFilterPanel(self):
		if not self.plotStatsAction.isChecked():
			self.updateDockView()
			return

		if not self.vl:
			QMessageBox.warning( self.iface.mainWindow(), "No layer loaded", u"Load a CSV layer and then try again." )
			self.plotStatsAction.setChecked(False)
			return

		self.resetActionsState()
		self.plotStatsAction.setChecked(True)

		self.createDock()
		self.updateDockView()

	def displayRoutinesPanel(self):
		if not self.routinesAction.isChecked():
			self.updateDockView()
			return

		if not self.vl:
			QMessageBox.warning( self.iface.mainWindow(), "No layer loaded", u"Load a CSV layer and then try again." )
			self.routinesAction.setChecked(False)
			return

		self.resetActionsState()
		self.routinesAction.setChecked(True)

		self.createDock()
		self.updateDockView()

