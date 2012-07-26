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

	def setupUi(self):
		layout = self.layout()

		spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout.addItem(spacer)

		self.plotBtn = QPushButton("Plot", self)
		QObject.connect( self.plotBtn, SIGNAL("clicked()"), self.plot )
		layout.addWidget(self.plotBtn)
	
	def recurrence(self, matrix):
		""" This method runs recurrence routines on the passed data """
		raise NotImplemented

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
		recurrence_table, stats, magn_interval = self.recurrence( data[:, indexes] )

		# create the plot dialog displaying magnitude vs. number of events 
		# and the line defined by bval and a_m values
		plot = RecurrencePlotDlg( parent=None, title="Recurrence", labels=("Magnitude", "Number of earthquakes") )
		plot.setData( recurrence_table[:, 0], recurrence_table[:, 1], info=(magn_interval, stats) )

		return plot


class WeichertRecurrenceWdg(RecurrenceWdg):

	def __init__(self, parent=None):
		RecurrenceWdg.__init__(self, parent)
		self.setupUi()
		self.algorithmName = "weichert_recurrence"

	def setupUi(self):
		layout = QVBoxLayout(self)

		label = QLabel("Reference magnitude", self)
		layout.addWidget(label)

		self.reference_magn = QLineEdit("4.0", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.1 )
		self.reference_magn.setValidator( validator )
		layout.addWidget(self.reference_magn)

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

		self.setLayout(layout)
		return RecurrenceWdg.setupUi(self)

	def recurrence(self, matrix):
		return self.weichert_recurrence(matrix)

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
		magn_window = float(self.magn_window.text())
		reference_magn = float(self.reference_magn.text())
		time_window = float(self.time_window.text())

		# calculate completeness table
		from .mtoolkit.scientific.completeness import stepp_analysis
		completeness_table = stepp_analysis(year, magnitude, magn_window, time_window)

		# run now!
		from .mtoolkit.scientific.recurrence import recurrence_analysis, recurrence_table
		stats = recurrence_analysis(year, magnitude, completeness_table, magn_window, "Weichert", reference_magn, time_window)
		rec_table = recurrence_table(magnitude, magn_window, year)[:, (0,3)]

		return rec_table, stats, magn_window


class AkiRecurrenceWdg(RecurrenceWdg):

	def __init__(self, parent=None):
		RecurrenceWdg.__init__(self, parent)
		self.setupUi()
		self.algorithmName = "aki_recurrence"

	def setupUi(self):
		layout = QVBoxLayout(self)

		label = QLabel("Reference magnitude", self)
		layout.addWidget(label)

		self.reference_magn = QLineEdit("4.0", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.1 )
		self.reference_magn.setValidator( validator )
		layout.addWidget(self.reference_magn)

		label = QLabel("Magnitude interval", self)
		layout.addWidget(label)

		self.magn_window = QLineEdit("0.1", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0.1 )
		self.magn_window.setValidator( validator )
		layout.addWidget(self.magn_window)

		self.setLayout(layout)
		return RecurrenceWdg.setupUi(self)

	def recurrence(self, matrix):
		return self.aki_recurrence(matrix)

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
		magn_window = float(self.magn_window.text())
		reference_magn = float(self.reference_magn.text())

		# calculate completeness table
		from .mtoolkit.scientific.completeness import stepp_analysis
		completeness_table = stepp_analysis(year, magnitude, magn_window)

		# run now!
		from .mtoolkit.scientific.recurrence import recurrence_analysis, recurrence_table
		stats = recurrence_analysis(year, magnitude, completeness_table, magn_window, "MLE", reference_magn, None)
		rec_table = recurrence_table(magnitude, magn_window, year)[:, (0,3)]

		return rec_table, stats, magn_window



from plot_wdg import PlotDlg, PlotWdg

class RecurrencePlotDlg(PlotDlg):
	def createPlot(self, *args, **kwargs):
		return RecurrencePlotWdg(*args, **kwargs)

class RecurrencePlotWdg(PlotWdg):
	def _plot(self):
		""" convert values, then create the plot """

		# plot the magnitude vs. event count bar graphic
		magn_interval = self.info[0]
		bar_width = magn_interval - 0.01

		items = self.axes.bar( self.x, self.y, width=bar_width )
		self.collections.append( items )

		# plot a line defined by bval (slope) and a_m (intersection with y axis when Mw = 0)  
		bval, sigb, a_m, siga_m = self.info[1]

		line = self.axes.plot( (0, 10), (a_m, bval*10+a_m), lw=3., color='r', alpha=0.4 )
		#self.axes.add_line(line)

		# plot line uncertainty bounds
		line = self.axes.plot( (0, 10), (a_m+siga_m, (bval+sigb)*10+(a_m+siga_m)), lw=1., color='r', ls='--', alpha=0.8 )
		#self.axes.add_line(line)

		line = self.axes.plot( (0, 10), (a_m-siga_m, (bval-sigb)*10+(a_m-siga_m)), lw=1., color='r', ls='--', alpha=0.8 )
		#self.axes.add_line(line)

