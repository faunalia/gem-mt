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

from qgis.core import QGis, QgsVectorLayer
from utils import Utils, LayerStyler

import resources_rc

class GEM_MT_Plugin:

	def __init__(self, iface):
		self.iface = iface
		self.toolbar = None

		self.vl = None
		self.basemapVl = None
		self.filterDock = None
		self.classificationDock = None

	def initGui(self):
		# create the actions
		self.loadCsvAction = QAction( "Load CSV file", self.iface.mainWindow() )	#QIcon( ":/gem-mt_plugin/icons/loadCsv.png" )
		QObject.connect( self.loadCsvAction, SIGNAL( "triggered()" ), self.loadCsv )

		self.useActiveLayerAction = QAction( "Use active layer", self.iface.mainWindow() )	#QIcon( ":/gem-mt_plugin/icons/useActiveLayer.png" )
		QObject.connect( self.useActiveLayerAction, SIGNAL( "triggered()" ), self.useActiveLayer )

		self.plotStatsAction = QAction( "Plot statistics", self.iface.mainWindow() )	#QIcon( ":/gem-mt_plugin/icons/plotStats.png" )
		self.plotStatsAction.setCheckable(True)
		QObject.connect( self.plotStatsAction, SIGNAL( "toggled(bool)" ), self.displayFilterDock )

		self.classificationAction = QAction( "Classification", self.iface.mainWindow() )	#QIcon( ":/gem-mt_plugin/icons/classification.png" )
		self.classificationAction.setCheckable(True)
		QObject.connect( self.classificationAction, SIGNAL( "toggled(bool)" ), self.displayClassificationDock )


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
		self.iface.addPluginToMenu( "&GEM-MT Plugin", self.loadCsvAction )
		self.iface.addPluginToMenu( "&GEM-MT Plugin", self.useActiveLayerAction )
		self.iface.addPluginToMenu( "&GEM-MT Plugin", self.plotStatsAction )
		self.iface.addPluginToMenu( "&GEM-MT Plugin", self.classificationAction )
		self.iface.addPluginToMenu( "&GEM-MT Plugin", self.settingsAction )
		#self.iface.addPluginToMenu( "&GEM-MT Plugin", self.aboutAction )

	def unload(self):
		# delete the dockwidgets for filtering and classification
		self.destroyFilterDock()
		self.destroyClassificationDock()

		# remove the loaded layer if any
		if self.vl:
			QObject.disconnect( self.vl, SIGNAL("layerDeleted()"), self.layerDestroyed )
			self.vl = None

		# remove actions from toolbars and menus
		self.toolbar.removeAction( self.loadCsvAction )
		self.toolbar.removeAction( self.useActiveLayerAction )
		self.toolbar.removeAction( self.plotStatsAction )
		self.toolbar.removeAction( self.classificationAction )
		self.iface.removePluginMenu( "&GEM-MT Plugin", self.loadCsvAction )
		self.iface.removePluginMenu( "&GEM-MT Plugin", self.useActiveLayerAction )
		self.iface.removePluginMenu( "&GEM-MT Plugin", self.plotStatsAction )
		self.iface.removePluginMenu( "&GEM-MT Plugin", self.classificationAction )
		self.iface.removePluginMenu( "&GEM-MT Plugin", self.settingsAction )
		#self.iface.removePluginMenu( "&GEM-MT Plugin", self.aboutAction )

		# delete the custom toolbar
		self.toolbar.deleteLater()
		self.toolbar = None


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
		filename = QFileDialog.getOpenFileName(self.iface.mainWindow(), "Select a csv file", QString(), "CSV file (*.csv)")
		if filename.isEmpty():
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
		QObject.connect( self.vl, SIGNAL("layerDeleted()"), self.layerDestroyed )

		# enable the filter/plot panel
		self.plotStatsAction.setChecked(True)

	def removeLayer(self):
		if self.vl:
			# destroy the filter/plot and classification panels
			self.destroyFilterDock()
			self.destroyClassificationDock()

			QObject.disconnect( self.vl, SIGNAL("layerDeleted()"), self.layerDestroyed )
			#QgsMapLayerRegistry.instance().removeMapLayer( self.vl.id() )
			self.vl = None

	def layerDestroyed(self):
		self.destroyFilterDock()
		self.destroyClassificationDock()
		self.vl = None



	def displayFilterDock(self):
		if not self.plotStatsAction.isChecked():
			if self.filterDock:
				self.filterDock.close()
			return

		if not self.vl:
			QMessageBox.warning( self.iface.mainWindow(), "No layer loaded", u"Load a CSV layer and then try again." )
			self.plotStatsAction.setChecked(False)
			return

		if not self.filterDock:
			from filter_wdg import FilterDock
			self.filterDock = FilterDock(self.iface, self.vl)
			QObject.connect(self.filterDock, SIGNAL("closed"), self.onFilterDockClosed)

		# display a dock widget at one time
		if self.classificationDock and self.classificationDock.isVisible():
			self.iface.mapCanvas().freeze(True)
			self.classificationAction.setChecked(False)

		if not self.filterDock.isVisible():
			self.iface.addDockWidget(Qt.RightDockWidgetArea, self.filterDock)

		if self.classificationDock and self.iface.mapCanvas().isFrozen():
			self.iface.mapCanvas().freeze(False)


	def onFilterDockClosed(self):
		self.plotStatsAction.setChecked(False)

	def destroyFilterDock(self):
		if self.filterDock:
			self.filterDock.close()
			self.filterDock.deleteLater()
			self.filterDock = None

	def displayClassificationDock(self):
		if not self.classificationAction.isChecked():
			if self.classificationDock:
				self.classificationDock.close()
			return

		if not self.vl:
			QMessageBox.warning( self.iface.mainWindow(), "No layer loaded", u"Load a CSV layer and then try again." )
			self.classificationAction.setChecked(False)
			return

		if not self.classificationDock:
			from classification_wdg import ClassificationDock
			self.classificationDock = ClassificationDock(self.iface, self.vl)
			QObject.connect(self.classificationDock, SIGNAL("closed"), self.onClassificationDockClosed)

		if self.filterDock and self.filterDock.isVisible():
			self.iface.mapCanvas().freeze(True)
			self.plotStatsAction.setChecked(False)

		if not self.classificationDock.isVisible():
			self.iface.addDockWidget(Qt.RightDockWidgetArea, self.classificationDock)

		if self.filterDock and self.iface.mapCanvas().isFrozen():
			self.iface.mapCanvas().freeze(False)


	def onClassificationDockClosed(self):
		self.classificationAction.setChecked(False)

	def destroyClassificationDock(self):
		if self.classificationDock:
			self.classificationDock.close()
			self.classificationDock.deleteLater()
			self.classificationDock = None

