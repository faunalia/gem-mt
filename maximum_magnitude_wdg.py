# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name			 	 : GEM Modellers Toolkit plugin (GEM-MT)
Description          : Analysing and Processing Earthquake Catalogue Data
Date                 : Jul 18, 2012 
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

from utils import Utils, LayerStyler

import numpy as np


class MaximumMagnitudeWdg(QWidget):

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi()

	def setupUi(self):
		layout = QVBoxLayout(self)
		self.setLayout(layout)

		label = QLabel("Algorithm", self)
		layout.addWidget(label)

		self.algCombo = QComboBox(self)
		self.algCombo.addItems( ["Kijko", "Makropoulos & Burton" ] )
		layout.addWidget(self.algCombo)

		label = QLabel("Sigma magnitude field", self)
		layout.addWidget(label)

		layer = Utils.classifiedVl()
		self.combo = QComboBox(self)
		self.combo.addItem( "-- none --", -1 )
		fields = layer.dataProvider().fields()
		for idx in range(fields.count()):
			self.combo.addItem( fields[idx].name(), idx )
		layout.addWidget(self.combo)

		spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout.addItem(spacer)

		self.runBtn = QPushButton("Save to file", self)
		QObject.connect( self.runBtn, SIGNAL("clicked()"), self.toAscii )
		layout.addWidget(self.runBtn)


	def maximum_magnitude(self, *argv, **kwargs):
		""" This method runs decluster routine on the passed data. """
		algNum = self.algCombo.currentIndex()
		if algNum == 0:
			return self.kijko_maximum_magnitude(*argv, **kwargs)
		elif algNum == 1:
			return self.makropoulos_maximum_magnitude(*argv, **kwargs)
		raise NotImplemented

	def kijko_maximum_magnitude(self, matrix):
		""" This method runs kijko maximum magnitude routines on the data.

			@params:
				**matrix** matrix with these columns in order: 
					magnitude, sigma_magn (optional)
		"""

		# convert QVariant objects to proper values
		magnitude = np.vectorize(lambda x: float(x))(matrix[:, 0])
		if np.shape(matrix)[1] > 1:
			sigma_magn = np.vectorize(lambda x: float(x))(matrix[:, 1])
		else:
			sigma_magn = np.ones( np.shape(magnitude) ) * 0.1

		# default options
		iter_tol = 1.0E-5
		max_iter = 1000
		num_samples = 51
		neq = 100	#np.shape(magnitude)[0]

		# run now!
		from .mtoolkit.scientific.maximum_magnitude import kijko_nonparametric_gauss
		return kijko_nonparametric_gauss(magnitude, sigma_magn, neq, num_samples, iter_tol, max_iter, max_observed=False)


	def makropoulos_maximum_magnitude(self, matrix):
		""" This method runs makropoulos maximum magnitude routines on the data.

			@params:
				**matrix** matrix with these columns in order: 
					year, magnitude, sigma_magn (optional)
		"""

		# convert QVariant objects to proper values
		year = np.vectorize(lambda x: x.toDate().year())(matrix[:, 0])
		magnitude = np.vectorize(lambda x: float(x))(matrix[:, 1])

		if np.shape(matrix)[1] > 2:
			sigma_magn = np.vectorize(lambda x: float(x))(matrix[:, 2])
		else:
			sigma_magn = np.ones( np.shape(magnitude) ) * 0.1

		# default options
		num_bootstraps = 100	#int(self.num_bootstraps.text())
		sigma_magn = 0.1	#np.zeros(np.shape(magnitude)[0]) + np.std(magnitude)

		# run now!
		from .mtoolkit.scientific.maximum_magnitude import cum_mo_uncertainty
		return cum_mo_uncertainty(year, magnitude, sigma_magn, num_bootstraps)



	def requestData(self, fieldkeys):
		data, panMap, indexes = [], {}, []
		
		# ask for populating data and panMap objects
		self.emit( SIGNAL("dataRequested"), data, panMap )

		if len(data) <= 0:
			return

		# get indexes of fields required to execute the algorithm
		for f in fieldkeys:
			try:
				indexes.append( panMap[f] )
			except KeyError:
				QMessageBox.warning(self, "Processing", u"Cannot find the field containing the %s. Such field is required to execute the selected algorithm." % f)
				return

		# convert input data to a matrix
		data = np.array(data)

		return data, panMap, indexes

	def toAscii(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			ret = self._toAscii()
			if ret is None:
				return
		finally:
			QApplication.restoreOverrideCursor()

		# store the output to ascii files
		filename = QFileDialog.getSaveFileName( self, "Choose where to save the output", "", "ASCII file (*.txt)" )
		if filename == "":
			return

		if filename[-4:] != ".txt":
			filename += ".txt"

		max_magn, max_magn_sigma = ret

		with open( unicode(filename), 'w' ) as fout:
			fout.write( "max_magn:\n%s" % repr(max_magn) )
			fout.write( "\n\nmax_magn_sigma:\n%s" % repr(max_magn_sigma) )

	def _toAscii(self):
		if self.algCombo.currentIndex() == 0:
			required_fields = ['magnitude']
		else:
			required_fields = ['date', 'magnitude']

		req = self.requestData( required_fields )
		if req is None:
			return

		data, panMap, indexes = req

		sigma_field_idx = int ( self.combo.itemData(self.combo.currentIndex()) )
		if sigma_field_idx >= 0:
			indexes.append( sigma_field_idx )

		# run the algorithm
		max_magn, max_magn_sigma = self.maximum_magnitude( data[:, indexes] )
		return max_magn, max_magn_sigma

