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

class KijkoMaximumMagnitudeWdg(QWidget):

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi()
		self.algorithmName = "kijko_maximum_magnitude"

	def setupUi(self):
		layout = QVBoxLayout(self)

		label = QLabel("Iteration tolerance", self)
		layout.addWidget(label)

		self.iter_tol = QLineEdit("0.2", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.1 )
		self.iter_tol.setValidator( validator )
		layout.addWidget(self.iter_tol)

		label = QLabel("Maximum iteration", self)
		layout.addWidget(label)

		self.max_iter = QLineEdit("1000", self)
		validator = QIntValidator(self)
		validator.setBottom( 1 )
		self.max_iter.setValidator( validator )
		layout.addWidget(self.max_iter)

		label = QLabel("Number samples", self)
		layout.addWidget(label)

		self.num_samples = QLineEdit("4", self)
		validator = QIntValidator(self)
		validator.setBottom( 1 )
		self.num_samples.setValidator( validator )
		layout.addWidget(self.num_samples)

		spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout.addItem(spacer)

		self.runBtn = QPushButton("Run", self)
		QObject.connect( self.runBtn, SIGNAL("clicked()"), self.run )
		layout.addWidget(self.runBtn)

		self.setLayout(layout)

	def kijko_maximum_magnitude(self, matrix):
		""" This method runs kijko maximum magnitude routines on the data.

			@params:
				**matrix** matrix with these columns in order: 
					magnitude
		"""

		# convert QVariant objects to proper values
		magnitude = np.vectorize(lambda x: x.toDouble()[0])(matrix[:, 0])

		# get options
		iter_tol = float(self.iter_tol.text())
		max_iter = float(self.max_iter.text())
		num_samples = float(self.num_samples.text())

		neq = np.shape(magnitude)[0]
		sigma_magn = np.zeros(neq) + np.std(magnitude)

		# run now!
		from .mtoolkit.scientific.maximum_magnitude import kijko_nonparametric_gauss
		return kijko_nonparametric_gauss(magnitude, sigma_magn, neq, num_samples, iter_tol, max_iter, max_observed=False)


	def run(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			max_magn, max_magn_sigma = self._run()
		finally:
			QApplication.restoreOverrideCursor()

		# display result now!
		QMessageBox.information(self, "Maximum magnitude", "Stats:\n\nmax magnitude: %s\nmax magnitude sigma: %s" % (max_magn, max_magn_sigma))

	def _run(self):
		data, panMap = [], {}

		# ask for populating data and panMap objects
		self.emit( SIGNAL("dataRequested"), data, panMap )

		if len(data) <= 0:
			return

		# get indexes of fields required to execute the algorithm
		indexes = []
		for f in ['magnitude']:
			try:
				indexes.append( panMap[f] )
			except KeyError:
				QMessageBox.warning(self, "Processing", u"Cannot find the field containing the %s. Such field is required to execute the selected algorithm." % f)
				return

		# convert input data to a matrix
		data = np.array(data)

		# run the algorithm
		max_magn, max_magn_sigma = self.kijko_maximum_magnitude( data[:, indexes] )
		return max_magn, max_magn_sigma


class MakropoulosMaximumMagnitudeWdg(QWidget):

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi()
		self.algorithmName = "makropoulos_maximum_magnitude"

	def setupUi(self):
		layout = QVBoxLayout(self)

		label = QLabel("Number bootstraps", self)
		layout.addWidget(label)

		self.num_bootstraps = QLineEdit("10", self)
		validator = QIntValidator(self)
		validator.setBottom( 1 )
		self.num_bootstraps.setValidator( validator )
		layout.addWidget(self.num_bootstraps)

		spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout.addItem(spacer)

		self.runBtn = QPushButton("Run", self)
		QObject.connect( self.runBtn, SIGNAL("clicked()"), self.run )
		layout.addWidget(self.runBtn)

		self.setLayout(layout)

	def makropoulos_maximum_magnitude(self, matrix):
		""" This method runs makropoulos maximum magnitude routines on the data.

			@params:
				**matrix** matrix with these columns in order: 
					year, magnitude
		"""

		# convert QVariant objects to proper values
		year = np.vectorize(lambda x: x.toDate().year())(matrix[:, 0])
		magnitude = np.vectorize(lambda x: x.toDouble()[0])(matrix[:, 1])

		# get options
		num_bootstraps = int(self.num_bootstraps.text())

		sigma_magn = np.zeros(np.shape(magnitude)[0]) + np.std(magnitude)

		# run now!
		from .mtoolkit.scientific.maximum_magnitude import cum_mo_uncertainty
		return cum_mo_uncertainty(year, magnitude, sigma_magn, num_bootstraps)

	def run(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			max_magn, max_magn_sigma = self._run()
		finally:
			QApplication.restoreOverrideCursor()

		# display result now!
		QMessageBox.information(self, "Maximum magnitude", "Stats:\n\nmax magnitude: %s\nmax magnitude sigma: %s" % (max_magn, max_magn_sigma))

	def _run(self):
		data, panMap = [], {}

		# ask for populating data and panMap objects
		self.emit( SIGNAL("dataRequested"), data, panMap )

		if len(data) <= 0:
			return

		# get indexes of fields required to execute the algorithm
		indexes = []
		for f in ['date', 'magnitude']:
			try:
				indexes.append( panMap[f] )
			except KeyError:
				QMessageBox.warning(self, "Processing", u"Cannot find the field containing the %s. Such field is required to execute the selected algorithm." % f)
				return

		# convert input data to a matrix
		data = np.array(data)

		# run the algorithm
		max_magn, max_magn_sigma = self.makropoulos_maximum_magnitude( data[:, indexes] )
		return max_magn, max_magn_sigma

