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

class SteppCompletenessWdg(QWidget):

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi()
		self.algorithmName = "afteran_decluster"

	def setupUi(self):
		layout = QVBoxLayout(self)

		label = QLabel("Magnitude interval", self)
		layout.addWidget(label)

		self.magn_window = QLineEdit("0.1", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.1 )
		self.magn_window.setValidator( validator )
		layout.addWidget(self.magn_window)

		label = QLabel("Time window (in days)", self)
		layout.addWidget(label)

		self.time_window = QLineEdit("1", self)
		validator = QIntValidator(self)
		validator.setBottom( 1 )
		self.time_window.setValidator( validator )
		layout.addWidget(self.time_window)

		label = QLabel("Tolerance Threshold", self)
		layout.addWidget(label)

		self.tol_threshold = QLineEdit("0.2", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.1 )
		self.tol_threshold.setValidator( validator )
		layout.addWidget(self.tol_threshold)

		spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout.addItem(spacer)

		self.plotBtn = QPushButton("Plot", self)
		QObject.connect( self.plotBtn, SIGNAL("clicked()"), self.plot )
		layout.addWidget(self.plotBtn)

		self.setLayout(layout)

	def stepp_completeness(self, matrix):
		""" This method runs stepp completeness routines on the data.

			@params:
				**matrix** matrix with these columns in order: 
					year, magnitude
		"""

		# convert QVariant objects to proper values
		year = np.vectorize(lambda x: x.toDate().year())(matrix[:, 0])
		magnitude = np.vectorize(lambda x: x.toDouble()[0])(matrix[:, 1])

		# get options
		magn_window = float(self.magn_window.text())
		time_window = float(self.time_window.text())
		tol_threshold = float(self.tol_threshold.text())

		# run now!
		from .mtoolkit.scientific.completeness import stepp_analysis
		return stepp_analysis(year, magnitude, magn_window, time_window, tol_threshold)


	def plot(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			dlg = self._plot()
		finally:
			QApplication.restoreOverrideCursor()

		# plot clustered data!
		dlg.show()
		dlg.exec_()
		dlg.deleteLater()

	def _plot(self):
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
		completeness_table = self.stepp_completeness( data[:, indexes] )

		# create the plot dialog
		from plot_wdg import ScatterPlotDlg
		plot = ScatterPlotDlg( parent=None, title="Magnitude completeness", labels=("Magnitude", "Year") )
		plot.setData( completeness_table[:, 1], completeness_table[:, 0] )

		return plot

