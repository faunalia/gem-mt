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

class CompletenessWdg(QWidget):

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi()

	def setupUi(self):
		layout = QVBoxLayout(self)

		label = QLabel("Time window (years)", self)
		layout.addWidget(label)

		self.time_window = QLineEdit("1", self)
		validator = QIntValidator(self)
		validator.setBottom( 1 )
		self.time_window.setValidator( validator )
		layout.addWidget(self.time_window)

		label = QLabel("Magnitude bin width", self)
		layout.addWidget(label)

		self.magn_bin_width = QLineEdit("0.2", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.1 )
		self.magn_bin_width.setValidator( validator )
		layout.addWidget(self.magn_bin_width)

		label = QLabel("Sensitivity", self)
		layout.addWidget(label)

		self.sensitivity = QLineEdit("0.1", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.001 )
		self.sensitivity.setValidator( validator )
		layout.addWidget(self.sensitivity)

		self.increment_lock = QCheckBox("Increment lock", self)
		self.increment_lock.setChecked( True )
		layout.addWidget(self.increment_lock)

		spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout.addItem(spacer)

		self.toAsciiBtn = QPushButton("Save to file", self)
		QObject.connect( self.toAsciiBtn, SIGNAL("clicked()"), self.toAscii )
		layout.addWidget(self.toAsciiBtn)

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
		time_window = float(self.time_window.text())
		magn_bin_width = float(self.magn_bin_width.text())
		sensitivity = float(self.sensitivity.text())
		increment_lock = self.increment_lock.isChecked()

		# run now!
		from .mtoolkit.scientific.completeness import stepp_analysis
		return stepp_analysis(year, magnitude, magn_bin_width, time_window, sensitivity, increment_lock)

	def requestData(self, fieldkeys):
		data, panMap = [], {}

		# ask for populating data and panMap objects
		self.emit( SIGNAL("dataRequested"), data, panMap )

		if len(data) <= 0:
			return

		# get indexes of fields required to execute the algorithm
		indexes = []
		for f in fieldkeys:
			try:
				indexes.append( panMap[f] )
			except KeyError:
				QMessageBox.warning(self, "Processing", u"Cannot find the field containing the %s. Such field is required to execute the selected algorithm." % f)
				return

		# convert input data to a matrix
		data = np.array(data)

		return data, panMap, indexes


	def plot(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			dlg = self._plot()
			if dlg is None:
				return
		finally:
			QApplication.restoreOverrideCursor()

		# plot clustered data!
		dlg.show()
		dlg.exec_()
		dlg.deleteLater()

	def _plot(self):
		req = self.requestData( ['date', 'magnitude'] )
		if req is None:
			return
		data, panMap, indexes = req

		# run the algorithm
		completeness_table = self.stepp_completeness( data[:, indexes] )

		# create the plot dialog
		from plot_wdg import ScatterPlotDlg
		plot = CompletenessPlotDlg( parent=None, title="Magnitude completeness", labels=("Year", "Magnitude") )
		plot.setData( completeness_table[:, 0], completeness_table[:, 1] )

		return plot

	def toAscii(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			completeness_table = self._toAscii()
			if completeness_table is None:
				return
		finally:
			QApplication.restoreOverrideCursor()

		# store the output to ascii file
		filename = QFileDialog.getSaveFileName( self, "Choose where to save the output", QString(), "ASCII file (*.txt)" )
		if filename == "":
			return

		if filename[-4:] != ".txt":
			filename += ".txt"

		with open( unicode(filename), 'w' ) as fout:
			fout.write( repr(completeness_table) )


	def _toAscii(self):
		req = self.requestData( ['date', 'magnitude'] )
		if req is None:
			return
		data, panMap, indexes = req

		# run the algorithm
		completeness_table = self.stepp_completeness( data[:, indexes] )
		return completeness_table


from plot_wdg import PlotDlg, PlotWdg

class CompletenessPlotDlg(PlotDlg):
	def createPlot(self, *args, **kwargs):
		return CompletenessPlotWdg(*args, **kwargs)

class CompletenessPlotWdg(PlotWdg):
	def _plot(self):
		self.axes.step( self.x, self.y )

