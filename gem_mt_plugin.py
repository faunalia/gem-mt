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

#import resources_rc

class GEM_MT_Plugin:

	def __init__(self, iface):
		self.iface = iface
		self.toolbar = None

		self.vl = None
		self.filterDock = None
		self.classificationDock = None

	def initGui(self):
		# create the actions
		self.loadCsvAction = QAction( "Load CSV file", self.iface.mainWindow() )	#QIcon( ":/plugins/GEM-MT_plugin/icons/loadCsv.png" )
		QObject.connect( self.loadCsvAction, SIGNAL( "triggered()" ), self.loadCsv )

		self.plotStatsAction = QAction( "Plot statistics", self.iface.mainWindow() )	#QIcon( ":/plugins/GEM-MT_plugin/icons/plotStats.png" )
		self.plotStatsAction.setCheckable(True)
		QObject.connect( self.plotStatsAction, SIGNAL( "toggled(bool)" ), self.displayFilterDock )

		self.classificationAction = QAction( "Classification", self.iface.mainWindow() )	#QIcon( ":/plugins/GEM-MT_plugin/icons/classification.png" )
		self.classificationAction.setCheckable(True)
		QObject.connect( self.classificationAction, SIGNAL( "toggled(bool)" ), self.displayClassificationDock )


		self.settingsAction = QAction( "Settings", self.iface.mainWindow() )	#QIcon( ":/plugins/GEM-MT_plugin/icons/settings.png" )
		QObject.connect( self.settingsAction, SIGNAL( "triggered()" ), self.settings )

		self.aboutAction = QAction( "About", self.iface.mainWindow() )	#QIcon( ":/plugins/GEM-MT_plugin/icons/about.png" )
		QObject.connect( self.aboutAction, SIGNAL("triggered()"), self.about )

		# create a custom toolbar
		self.toolbar = self.iface.addToolBar( "GEM-MT Plugin" )

		# add actions to toolbars and menus
		self.toolbar.addAction( self.loadCsvAction )
		self.toolbar.addAction( self.plotStatsAction )
		self.toolbar.addAction( self.classificationAction )
		self.iface.addPluginToMenu( "&GEM-MT Plugin", self.loadCsvAction )
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
		self.toolbar.removeAction( self.plotStatsAction )
		self.toolbar.removeAction( self.classificationAction )
		self.iface.removePluginMenu( "&GEM-MT Plugin", self.loadCsvAction )
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

		# create the uri for the delimitedtext provider
		from .settings_dlg import Settings
		url = QUrl.fromLocalFile( filename )
		url.setQueryItems( [
			( "delimiter", Settings.delimiter() ),
			( "delimiterType", "regexp"),
			( "xField", Settings.longitudeField() ),
			( "yField", Settings.latitudeField() )
		] )

		# layer base name and path to style file
		baseName = QFileInfo(filename).baseName()
		dir_path = QFileInfo(filename).absoluteDir()
		style_path = dir_path.absoluteFilePath( u"%s.qml" % baseName )

		# store the current render flag state, then unset it
		prev_render_flag = self.iface.mapCanvas().renderFlag()
		self.iface.mapCanvas().setRenderFlag( False )

		try:
			from qgis.core import QGis, QgsVectorLayer, QgsMapLayerRegistry

			# load the layer
			vl = QgsVectorLayer(url.toString(), baseName, "delimitedtext")
			if not vl.isValid():	# invalid layer
				QMessageBox.warning( self.iface.mainWindow(), "Invalid layer", u"Unable to load the layer %s" % url.toString() )
				return

			if vl.geometryType() != QGis.Point:
				QMessageBox.warning( self.iface.mainWindow(), "Invalid CSV data", u"Unable to get data from the selected file. Setup Lat/Long field names and delimiter from the Settings dialog and then try again." )
				self.settings()
				return

			# set the layer style
			dir_path = QFileInfo(filename).absoluteDir()
			style_path = dir_path.absoluteFilePath( u"%s.qml" % baseName )
			vl.loadNamedStyle( style_path )

			# destroy the filter dock if any, then remove the previous loaded layer
			self.destroyFilterDock()
			if self.vl:
				QObject.disconnect( self.vl, SIGNAL("layerDeleted()"), self.layerDestroyed )
				QgsMapLayerRegistry.instance().removeMapLayer( self.vl.id() )
				self.vl = None

			# add the new layer to the map, then create a new filter dock
			if hasattr(QgsMapLayerRegistry.instance(), 'addMapLayers'):	# available from QGis >= 1.8
				QgsMapLayerRegistry.instance().addMapLayers( [ vl ] )
			else:
				QgsMapLayerRegistry.instance().addMapLayer( vl )
			self.vl = vl

			self.plotStatsAction.setChecked(True)

		finally:
			# restore the render flag state
			self.iface.mapCanvas().setRenderFlag( prev_render_flag )

		QObject.connect( self.vl, SIGNAL("layerDeleted()"), self.layerDestroyed )


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


	def layerDestroyed(self):
		self.destroyFilterDock()
		self.destroyClassificationDock()
		self.vl = None



	def defineArea(self):
		if not self.classificationAction.isChecked():
			return

		if not self.vl:
			QMessageBox.warning( self.iface.mainWindow(), "No layer loaded", u"Load a CSV layer and then try again." )
			self.classificationAction.setChecked(False)
			return

		if not self.areaDrawer:
			from MapTools import PolygonDrawer
			self.areaDrawer = PolygonDrawer(self.iface.mapCanvas(), {'color':QColor('black'), 'border':2, 'enableSnap':False, 'keepAfterEnd':True})
			self.areaDrawer.setAction( self.classificationAction )

		self.areaDrawer.startCapture()
	
	def createBufferMidline(self):
		if not self.createBufferMidlineAction.isChecked():
			return

		if not self.vl:
			QMessageBox.warning( self.iface.mainWindow(), "No layer loaded", u"Load a CSV layer and then try again." )
			self.createBufferMidlineAction.setChecked(False)
			return

		if not self.areaDrawer or not self.areaDrawer.isValid():
			QMessageBox.warning( self.iface.mainWindow(), "Missing Area of Interest", u"Define an Area of Interest and then try again." )
			self.createBufferMidlineAction.setChecked(False)
			return			

		if not self.segmentDrawer:
			from MapTools import SegmentDrawer
			self.segmentDrawer = SegmentDrawer(self.iface.mapCanvas(), {'color':QColor('aqua'), 'border':2, 'enableSnap':False, 'keepAfterEnd':True})
			self.segmentDrawer.setAction( self.createBufferMidlineAction )

		self.segmentDrawer.startCapture()
