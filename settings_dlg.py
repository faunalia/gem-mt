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

class Settings:
	@staticmethod
	def delimiter():
		return QSettings("/GEM-MT_plugin").value("delimiter", ",").toString()

	@staticmethod
	def longitudeField():
		return QSettings("/GEM-MT_plugin").value("long_field", "Longitude").toString()

	@staticmethod
	def latitudeField():
		return QSettings("/GEM-MT_plugin").value("lat_field", "Latitude").toString()

	@staticmethod
	def magnitudeField():
		return QSettings("/GEM-MT_plugin").value("magnitude_field", "Magnitude").toString()

	@staticmethod
	def depthField():
		return QSettings("/GEM-MT_plugin").value("depth_field", "Depth").toString()

	@staticmethod
	def dateField():
		return QSettings("/GEM-MT_plugin").value("date_field", "Date").toString()

	
	@staticmethod
	def key2indexFieldMap( fields ):
		key2index = {}

		for index, fld in fields.iteritems():
			key = Settings.fieldName2key( fld.name() )
			if key:
				key2index[ key ] = index

		return key2index

	@staticmethod
	def index2keyFieldMap( fields ):
		index2key = {}

		for index, fld in fields.iteritems():
			key = Settings.fieldName2key( fld.name() )
			if key:
				index2key[ index ] = key

		return index2key

	@staticmethod
	def fieldName2key( fieldName ):
		if not Settings.longitudeField().isEmpty() and \
				fieldName.startsWith( Settings.longitudeField(), Qt.CaseInsensitive ):
			return 'longitude'
		if not Settings.latitudeField().isEmpty() and \
				fieldName.startsWith( Settings.latitudeField(), Qt.CaseInsensitive ):
			return 'latitude'
		if not Settings.magnitudeField().isEmpty() and \
				fieldName.startsWith( Settings.magnitudeField(), Qt.CaseInsensitive ):
			return 'magnitude'
		if not Settings.depthField().isEmpty() and \
				fieldName.startsWith( Settings.depthField(), Qt.CaseInsensitive ):
			return 'depth'
		if not Settings.dateField().isEmpty() and \
				fieldName.startsWith( Settings.dateField(), Qt.CaseInsensitive ):
			return 'date'
		return None


from ui.settingsDlg_ui import Ui_Dialog
class SettingsDlg(QDialog, Ui_Dialog):
	def __init__(self, parent=None):
		super(SettingsDlg, self).__init__(parent)
		self.setupUi(self)

		# restore values
		settings = QSettings("/GEM-MT_plugin")
		self.delimiterCombo.setEditText( Settings.delimiter() )
		self.longEdit.setText( Settings.longitudeField() )
		self.latEdit.setText( Settings.latitudeField() )
		self.magnitudeEdit.setText( Settings.magnitudeField() )
		self.depthEdit.setText( Settings.depthField() )
		self.dateEdit.setText( Settings.dateField() )

	def accept(self):
		# store new values
		settings = QSettings("/GEM-MT_plugin")
		settings.setValue("delimiter", self.delimiterCombo.currentText())
		settings.setValue("long_field", self.longEdit.text())
		settings.setValue("lat_field", self.latEdit.text())
		settings.setValue("magnitude_field", self.magnitudeEdit.text())
		settings.setValue("depth_field", self.depthEdit.text())
		settings.setValue("date_field", self.dateEdit.text())

		super(SettingsDlg, self).accept()

