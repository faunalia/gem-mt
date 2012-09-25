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

from utils import Utils

import numpy as np

class RecurrenceWdg(QWidget):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi()

	def setupUi(self):
		layout = QVBoxLayout(self)
		self.setLayout(layout)

		label = QLabel("Algorithm", self)
		layout.addWidget(label)

		self.algCombo = QComboBox(self)
		self.algCombo.addItems( ["Weichert", "Aki" ] )
		layout.addWidget(self.algCombo)

		#self.addAlgOptions()
		#QObject.connect(self.algCombo, SIGNAL("currentIndexChanged(int)"), self.stacked.setCurrentIndex)

		spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout.addItem(spacer)

		self.toAsciiBtn = QPushButton("Save to file", self)
		QObject.connect( self.toAsciiBtn, SIGNAL("clicked()"), self.toAscii )
		layout.addWidget(self.toAsciiBtn)

		self.plotBtn = QPushButton("Plot", self)
		QObject.connect( self.plotBtn, SIGNAL("clicked()"), self.plot )
		layout.addWidget(self.plotBtn)


	def addAlgOptions(self):
		label = QLabel("Reference magnitude", self)
		self.layout().addWidget(label)

		self.reference_magn = QLineEdit("1.1", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.1 )
		self.reference_magn.setValidator( validator )
		self.layout().addWidget(self.reference_magn)

		label = QLabel("Magnitude interval", self)
		self.layout().addWidget(label)

		self.magn_window = QLineEdit("0.2", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.1 )
		self.magn_window.setValidator( validator )
		self.layout().addWidget(self.magn_window)

		self.stacked = QStackedWidget(self)
		self.layout().addWidget( self.stacked )

		widget = QWidget(self)
		layout = QVBoxLayout(widget)
		self.stacked.addWidget(widget)

		label = QLabel("Time window", self)
		layout.addWidget(label)

		self.time_window = QLineEdit("0.2", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.1 )
		self.time_window.setValidator( validator )
		layout.addWidget(self.time_window)

		widget = QWidget(self)
		layout = QVBoxLayout(widget)
		self.stacked.addWidget(widget)

	
	def recurrence(self, *argv, **kwargs):
		""" This method runs recurrence routines on the passed data """
		if self.algCombo.currentIndex() == 0:
			return self.weichert_recurrence(*argv, **kwargs)
		else:
			return self.aki_recurrence(*argv, **kwargs)

	def weichert_recurrence(self, matrix):
		""" This method runs recurrence routines on the data.

			@params:
				**matrix** matrix with these columns in order: 
					year, magnitude
		"""

		# convert QVariant objects to proper values
		year = np.vectorize(lambda x: x.toDate().year())(matrix[:, 0])
		magnitude = np.vectorize(lambda x: x.toDouble()[0])(matrix[:, 1])

		# get options
		magn_window = 0.2	#float(self.magn_window.text())
		reference_magn = 1.1	#float(self.reference_magn.text())
		time_window = 0.1	#float(self.time_window.text())

		# calculate completeness table
		from .mtoolkit.scientific.completeness import stepp_analysis
		completeness_table = stepp_analysis(year, magnitude)

		# run now!
		from .mtoolkit.scientific.recurrence import recurrence_analysis, recurrence_table
		stats = recurrence_analysis(year, magnitude, completeness_table, magn_window, "Weichert", reference_magn, time_window)
		rec_table = recurrence_table(magnitude, magn_window, year)

		return rec_table, stats

	def aki_recurrence(self, matrix):
		""" This method runs aki recurrence routines on the data.

			@params:
				**matrix** matrix with these columns in order: 
					year, magnitude
		"""

		# convert QVariant objects to proper values
		year = np.vectorize(lambda x: x.toDate().year())(matrix[:, 0])
		magnitude = np.vectorize(lambda x: x.toDouble()[0])(matrix[:, 1])

		# get options
		magn_window = 0.2	#float(self.magn_window.text())
		reference_magn = 1.1	#float(self.reference_magn.text())

		# calculate completeness table
		from .mtoolkit.scientific.completeness import stepp_analysis
		completeness_table = stepp_analysis(year, magnitude)

		# run now!
		from .mtoolkit.scientific.recurrence import recurrence_analysis, recurrence_table
		stats = recurrence_analysis(year, magnitude, completeness_table, magn_window, "MLE", reference_magn, None)
		rec_table = recurrence_table(magnitude, magn_window, year)

		return rec_table, stats


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
		recurrence_table, stats = self.recurrence( data[:, indexes] )

		# create the plot dialog displaying magnitude vs. number of events 
		# and the line defined by bval and a_m values
		plot = RecurrencePlotDlg( parent=None, title="Recurrence", labels=("Magnitude", "Number of earthquakes") )
		plot.setData( recurrence_table[:, 0], recurrence_table[:, (1,2)], info=stats )

		return plot


	def toAscii(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			ret = self._toAscii()
			if ret is None:
				return
		finally:
			QApplication.restoreOverrideCursor()

		# store the output to ascii file
		filename = QFileDialog.getSaveFileName( self, "Choose where to save the output", QString(), "ASCII file (*.txt)" )
		if filename == "":
			return

		if filename[-4:] != ".txt":
			filename += ".txt"

		bval, sigb, a_m, siga_m = ret

		with open( unicode(filename), 'w' ) as fout:
			fout.write( "a, sigma_a, b, sigma_b:\n" )
			fout.write( "%s, %s, %s, %s" % (a_m, siga_m, bval, sigb) )


	def _toAscii(self):
		req = self.requestData( ['date', 'magnitude'] )
		if req is None:
			return
		data, panMap, indexes = req

		# run the algorithm
		recurrence_table, stats = self.recurrence( data[:, indexes] )
		return stats


from plot_wdg import PlotDlg, PlotWdg

class RecurrencePlotDlg(PlotDlg):
	def createPlot(self, *args, **kwargs):
		return RecurrencePlotWdg(*args, **kwargs)

class RecurrencePlotWdg(PlotWdg):
	def _plot(self):
		""" convert values, then create the plot """
		# plot the magnitude vs. cumulative number of observations
		self.axes.plot( self.x, self.y[:, 1], ls='None', marker='s', color='w' )

		# plot the magnitude vs. number of observations
		self.axes.plot( self.x, self.y[:, 0], ls='None', marker='^', color='k' )

		# plot a line defined by bval (slope) and a_m (intersection with y axis 
		# when Mw = 0): logN = a_m - bval*M
		bval, sigb, a_m, siga_m = self.info

		def limitData(a, b):
			x = np.array( np.arange(0, 10, 0.01) )
			logy = a - x * b

			# limit output y values, this will avoid to reach inf
			indexes = np.logical_and(logy < 200, logy > -1)
			return x[indexes], np.power(10, logy[indexes])

		l_x, l_y = limitData( a_m, bval )
		line = self.axes.plot( l_x, l_y, lw=3., color='r', alpha=0.4, scalex=False, scaley=False )

		# plot line uncertainty bounds
		#l_x, l_y = limitData( a_m+siga_m, bval+sigb )
		#self.axes.plot( l_x, l_y, lw=1., color='r', ls='--', alpha=0.8 )
		#l_x, l_y = limitData( a_m-siga_m, bval-sigb )
		#self.axes.plot( l_x, l_y, lw=1., color='r', ls='--', alpha=0.8 )

		self.axes.set_yscale("log")

		self.axes.legend( [line], ["a: %s - sigma(a): %s\nb: %s - sigma(b): %s" % (a_m, siga_m, bval, sigb)], 
				'upper right', shadow=False, fancybox=False )

