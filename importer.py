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

from utils import Utils

class Importer(QObject):

	def __init__(self, inLayer, outUri, parent=None):
		QObject.__init__(self, parent)
		self.inLayer = inLayer
		self.outUri = outUri

		self._retCode = None
		self._errorMsg = None

		self.eventLoop = QEventLoop()

		self.progressDlg = QProgressDialog(self.parent())
		self.progressDlg.setModal(True)
		self.progressDlg.setWindowTitle("Importing data...")
		self.progressDlg.setLabelText("Please wait...")
		self.progressDlg.setAutoClose(True)
		self.progressDlg.setMinimumDuration(1000)
		QObject.connect(self.progressDlg, SIGNAL("canceled()"), self.cancel)
		# no progress is shown by default
		self.progressDlg.setRange(0,0)
		self.progressDlg.reset()

	def destroy(self, *args):
		self.progressDlg.deleteLater()
		self.eventLoop.deleteLater()

	def errorMessage(self):
		return self._errorMsg

	def wasCanceled(self):
		return self.progressDlg.wasCanceled()

	def start(self):
		self.progressDlg.show()
		try:
			return self.run()
		finally:
			self.progressDlg.accept()

	def run(self):
		raise NotImplemented

	def cancel(self):
		raise NotImplemented


class Ogr2ogrImporter(Importer):
	def run(self):
		outPath = unicode(self.outUri.database())
		inPath = unicode(self.inLayer.source())

		tempVrt = None
		if self.inLayer.providerType() == 'delimitedtext':
			# create the VRT which wraps the csv
			tempVrt = QTemporaryFile( u"%s/gem_mt_XXXXXX.vrt" % QDir.tempPath() )
			tempVrt.setAutoRemove(False)
			if not tempVrt.open( QIODevice.WriteOnly ):
				return False

			inPath = QUrl(inPath).toLocalFile()
			layerName = QFileInfo(inPath).baseName()
			vrtData = u"""<OGRVRTDataSource>
    <OGRVRTLayer name="%s">
        <SrcDataSource>%s</SrcDataSource>
        <GeometryType>wkbPoint</GeometryType>
        <LayerSRS>WGS84</LayerSRS>""" % (layerName, inPath)
			tempVrt.write( vrtData )

			from settings_dlg import Settings
			longField = Settings.longitudeField()
			latField = Settings.latitudeField()
			vrtData = u"""
        <GeometryField encoding="PointFromColumns" x="%s" y="%s"/>""" % (longField, latField)
			tempVrt.write( vrtData )

			def ogrTypeName(fld):
				if fld.type() == QVariant.Int:
					return "Integer"
				elif fld.type() == QVariant.Double:
					return  "Real"
				return "String"

			# add fields definition
			for index, fld in self.inLayer.dataProvider().fields().iteritems():
				vrtData = u"""
        <Field name="%s" type="%s"/>""" % (fld.name(), ogrTypeName(fld))
				tempVrt.write( vrtData )

			vrtData = u"""
    </OGRVRTLayer>
</OGRVRTDataSource>"""
			tempVrt.write( vrtData )

			tempVrt.close()

			inPath = unicode(tempVrt.fileName())
		
		self.process = QProcess()
		QObject.connect( self.process, SIGNAL("finished(int, QProcess::ExitStatus)"),  self._processFinished )

		self.process.start("ogr2ogr", ["-f","SQLite", "-dsco","SPATIALITE=YES", "-gt","65535", "-overwrite", outPath, inPath])
		print "ogr2ogr", " ".join(["-f","SQLite", "-dsco","SPATIALITE=YES", "-gt","65535", "-overwrite", outPath, inPath])
		self.eventLoop.exec_()

		# cleanup
		self._cancelProcess()

		if tempVrt:
			tempVrt.remove()
			tempVrt.deleteLater()
		tempVrt = None

		return self._retCode == 0

	def cancel(self):
		self._cancelProcess()
		self.eventLoop.quit()

	def _processFinished(self, retCode, exitStatus):
		self._retCode = retCode
		self._errorMsg = u"The import process ended with error #%d" % self.sender().error()
		self.eventLoop.quit()

	def _cancelProcess(self):
		if getattr(self, 'process', None):
			QObject.disconnect( self.process, SIGNAL("finished(int, QProcess::ExitStatus)"), self._processFinished )
			self.process.close()
			self.process.deleteLater()
			self.process = None


class QGisLayerImporter(Importer):
	def run(self):
		self.importThread = QGisLayerImporter.ImportThread(self.inLayer, self.outUri)
		QObject.connect( self.importThread, SIGNAL("importFinished"), self._importFinished )

		self.importThread.start()
		self.eventLoop.exec_()

		# cleanup
		self._cancelImport()

		return self._retCode == 0

	def cancel(self):
		self._cancelImport()
		self.eventLoop.quit()

	def _importFinished(self, retCode, errorMsg):
		self._retCode = retCode
		self._errorMsg = u"Error %d\n%s" % (retCode, errorMsg)
		self.eventLoop.quit()

	def _cancelImport(self):
		if getattr(self, 'importThread', None):
			QObject.disconnect( self.importThread, SIGNAL("importFinished"), self._importFinished )
			self.importThread.terminate()
			self.importThread.deleteLater()
			self.importThread = None


	class ImportThread(QThread):
		def __init__(self, inLayer, outUri):
			QThread.__init__(self)
			self.inLayer = inLayer
			self.outUri = outUri

		def run(self):
			try:
				self._run()
			except Exception, e:
				QgsMessageLog.instance().logMessage(u"Uncaught exception.\n%s" % unicode(e), "GEM-MT")
				self.emit( SIGNAL("importFinished"), -2, "An error occurred" )

		def _run(self):			
			path = self.outUri.database()
			# create the SL database if it doesn't exist
			f = QFile( path )
			if not f.exists():
				from pyspatialite import dbapi2 as sqlite
				try:
					conn = sqlite.connect( unicode(path) )
					conn.cursor().execute( "SELECT InitSpatialMetadata()" )
					conn.commit()
					del conn

				except Exception, e:
					# if an error occurs, remove the database file
					if f.exists():
						f.remove()

					msg = u"Unable to create the database %s. \nError was: %s" % (path, unicode(e) )
					self.emit( SIGNAL("importFinished"), -1, msg )
					return

			# import the CSV data to the SL database
			from qgis.core import QgsVectorLayerImport
			ret, errMsg = QgsVectorLayerImport.importLayer( self.inLayer, self.outUri.uri(), 'spatialite', self.inLayer.crs(), False, False, {'overwrite':True} )
			self.emit( SIGNAL("importFinished"), ret, errMsg )


class CsvToSL(QObject):

	OK, ERROR, CANCELED, INVALID_INPUT, INVALID_LATLON = range(5)

	def __init__(self, filename, parent=None):
		QObject.__init__(self, parent)
		self._fn = filename

	def run(self):
		# layer base name and dir path
		base_name = QFileInfo(self._fn).baseName()
		dir_path = QFileInfo(self._fn).absoluteDir()

		# create the uri for the delimitedtext provider
		from .settings_dlg import Settings
		csvUrl = QUrl.fromLocalFile( self._fn )
		csvUrl.setQueryItems( [
			( "delimiter", Settings.delimiter() ),
			( "delimiterType", "plain"),
			( "xField", Settings.longitudeField() ),
			( "yField", Settings.latitudeField() )
		] )

		# load the layer
		from qgis.core import QgsVectorLayer
		csvVl = QgsVectorLayer(csvUrl.toString(), base_name, "delimitedtext")
		if not csvVl.isValid():	# invalid layer
			csvVl.deleteLater()
			QMessageBox.warning( self.parent(), "Invalid layer", 
								u"Unable to load the layer %s" % self._fn )
			return (self.INVALID_INPUT, None)

		# check the layer geometry type
		from qgis.core import QGis
		if csvVl.geometryType() != QGis.Point:
			csvVl.deleteLater()
			QMessageBox.warning( self.parent(), "Invalid layer", 
								u"Unable to get data from the selected file. \nSetup Lat/Long field names and delimiter from the Settings dialog, \nthen try again." )
			return (self.INVALID_LATLON, None)

		# check whether the CSV file has to be imported to SL db
		if not Settings.importCsvToSl():
			return (self.OK, csvVl)

		# uri pointing to the new SL database
		from qgis.core import QgsDataSourceURI
		sqlite_path = dir_path.absoluteFilePath( u"%s.sqlite" % base_name )
		slUri = QgsDataSourceURI()
		slUri.setDatabase( sqlite_path )
		slUri.setDataSource( "", base_name, "GEOMETRY" )

		importer = Ogr2ogrImporter(csvVl, slUri, self.parent())
		#importer = QGisLayerImporter(csvVl, slUri, self.parent())
		ret = importer.start()

		# get the importer exit code
		if not ret:
			if importer.wasCanceled():
				ret = self.CANCELED
			else:
				ret = self.ERROR
		else:
			ret = self.OK

		# cleanup
		importer.deleteLater()
		importer = None

		csvVl.deleteLater()
		csvVl = None

		if ret != self.OK:
			return (ret, None)

		# load the layer from the SL database
		slVl = QgsVectorLayer(slUri.uri(), slUri.table(), "spatialite")
		if not slVl.isValid():	# invalid layer
			slVl.deleteLater()
			QMessageBox.warning( self.parent(),	"Invalid layer",
								u"Unable to load the layer %s" % slUri.database() )
			return (self.ERROR, None)

		# check the layer geometry type
		if slVl.geometryType() != QGis.Point:
			slVl.deleteLater()
			return (self.ERROR, None)

		return (self.OK, slVl)


