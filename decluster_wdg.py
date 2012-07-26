# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name			 	 : GEM Modellers Toolkit plugin (GEM-MT)
Description          : Analysing and Processing Earthquake Catalogue Data
Date                 : Jul 15, 2012 
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

class DeclusterWdg(QWidget):

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)

	def setupUi(self):
		layout = self.layout()

		spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout.addItem(spacer)

		self.plotBtn = QPushButton("Plot", self)
		QObject.connect( self.plotBtn, SIGNAL("clicked()"), self.plot )
		layout.addWidget(self.plotBtn)

		self.loadAsLayerBtn = QPushButton("Add to canvas", self)
		QObject.connect( self.loadAsLayerBtn, SIGNAL("clicked()"), self.loadAsLayer )
		layout.addWidget(self.loadAsLayerBtn)


	def decluster(self, matrix):
		""" This method runs decluster routine on the passed data. """
		raise NotImplemented

	@staticmethod
	def _fromAlgOutputData(vcl, vmain_shock, flagvector):
		""" convert the list of non-clustered events to a list of information
			used by the plugin.

			returns:
				**vcl** vector indicating cluster number for the input events
				**vncl_idx** indexes of clustered events
				**vcl_info** ndarray with columns containing:
					cluster number, cluster event count """

		vncl_idx = np.flatnonzero(flagvector == 0)	# non-clustered events indexes in vcl
		vcl_num = vcl[vncl_idx]	# cluster number of non-clustered events in vmain_shock 

		# get the count of events belong to each cluster (position 0 contains non-clustered events count) 
		vcl_evcnt = np.bincount(vcl)
		vcl_evcnt[0] = 1	# set event count to 1 for events not belong to a cluster

		# put together cluster num and number of events belongs to it
		vcl_info = np.column_stack( (vcl_num, vcl_evcnt[vcl_num]) )

		return vcl, vncl_idx, vcl_info


	@staticmethod
	def _toAlgInputData(data):
		""" Convert data to be used with decluster routines.

			@param:
				**data** matrix with these columns in order: 
					longitude (QVariant), latitude (QVariant), 
					magnitude (QVariant), date (QVariant)

			@return:
				 matrix with these columns in order: 
					year (int), month (int), day (int), 
					longitude (double), latitude (double), magnitude (double)
		"""

		neq = np.shape(data)[0]	# number of earthquakes

		# pre-allocate the out matrix
		matrix = np.zeros( (neq, 6) )

		# convert QVariant objects to proper values
		def toDateParts(date):
			""" convert QVariant date object to (year, month, day) tuple """
			d = date.toDate().toPyDate()
			return d.year, d.month, d.day

		year, month, day = np.vectorize(toDateParts)(data[:, 3])
		matrix[:, 0] = year.T	# add year
		matrix[:, 1] = month.T	# add month
		matrix[:, 2] = day.T	# add day

		# add longitude, latitude, magnitude
		matrix[:, 3:6] = np.vectorize(lambda x: x.toDouble()[0])(data[:, 0:3])

		return matrix

	def loadAsLayer(self):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

		# store the current render flag state, then unset it
		prev_render_flag = Utils.iface.mapCanvas().renderFlag()
		Utils.iface.mapCanvas().setRenderFlag( False )
		try:
			self._loadAsLayer()
		finally:
			# restore render flag state and cursor
			Utils.iface.mapCanvas().setRenderFlag( prev_render_flag )
			QApplication.restoreOverrideCursor()

	def _loadAsLayer(self):
		data, panMap = [], {}

		# ask for populating data and panMap objects
		self.emit( SIGNAL("dataRequested"), data, panMap )

		if len(data) <= 0:
			return

		# get indexes of fields required to execute the algorithm
		indexes = []
		for f in ['longitude','latitude','magnitude','date']:
			try:
				indexes.append( panMap[f] )
			except KeyError:
				QMessageBox.warning(self, "Processing", u"Cannot find the field containing the %s. Such field is required to execute the selected algorithm." % f)
				return

		# convert input data to the matrix used to feed the algorithm
		data = np.array(data)
		inmatrix = DeclusterWdg._toAlgInputData( data[:, indexes] )

		# run the algorithm, then get clusters data
		out_args = self.decluster( inmatrix )
		origdata_clnum, cldata_indexes, cl_info = DeclusterWdg._fromAlgOutputData( *out_args )

		# clusters data: append the cluster info to clustered events matrix
		clusters = np.concatenate( (data[cldata_indexes], cl_info), axis=1 )

		# original data: append the cluster number each the event belongs to
		original = np.concatenate( (data, origdata_clnum.reshape((-1, 1))), axis=1 )

		# create a group containing this routine's output layers, but first 
		# set the events layer as current one to avoid nested groups
		Utils.iface.setActiveLayer( Utils.eventsVl() )
		legend = Utils.iface.legendInterface()
		groupN = legend.addGroup( self.algorithmName )

		# now create both the original and clusters layers
		layers = {'original' : original, 'clusters' : clusters}
		for name, datamatrix in layers.iteritems():
			# make the layer from scratch, then add it to the canvas
			vl = self._createOutputLayer( name, datamatrix, panMap['longitude'], panMap['latitude'], name == 'original' )
			Utils.addVectorLayer( vl )

			# finally put the layer into the group
			# NB: the group number is incremented by one because the layer 
			# was added above the group in the legend
			legend.moveLayer(vl, groupN+1)

		legend.setGroupExpanded( groupN, False )


	def _createOutputLayer(self, name, data, longFieldIdx, latFieldIdx, isOrigLayer=False):
		""" create the declustered event layer:
			param:
				**isOrigLayer** whether True the layer will contain unclustered data """
		from qgis.core import QgsField, QgsFeature, QgsPoint, QgsGeometry

		clusterNum = "clusterNum"
		sizeField = "eventCount"

		fields = map( lambda x: x[1], sorted(Utils.classifiedVl().dataProvider().fields().iteritems()) )
		fields += [ QgsField(clusterNum, QVariant.Int) ]	# add the cluster num field

		if not isOrigLayer:
			fields += [ QgsField(sizeField, QVariant.Int) ]	# add the event count as last field

		# create the layer
		vl = Utils.createMemoryLayer( 'Point', 'epsg:4326', fields, name )
		if not vl:
			return

		# add features
		pr = vl.dataProvider()
		for row in data:
			attrs = dict(enumerate(row[1:].tolist()))
			point = QgsPoint( row[longFieldIdx].toDouble()[0], row[latFieldIdx].toDouble()[0] )

			f = QgsFeature()
			f.setAttributeMap( attrs )
			f.setGeometry( QgsGeometry.fromPoint( point ) )

			pr.addFeatures( [f] )

		# update layer's extent when new features have been added
		# because change of extent in provider is not propagated to the layer
		vl.updateExtents()

		# set layer style
		if isOrigLayer:
			LayerStyler.setSimpleStyle( vl, color=QColor('blue'), size=1.0 )
		else:
			LayerStyler.setDeclusteredStyle( vl, sizeField )

		return vl


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
		for f in ['longitude','latitude','magnitude','date']:
			try:
				indexes.append( panMap[f] )
			except KeyError:
				QMessageBox.warning(self, "Processing", u"Cannot find the field containing the %s. Such field is required to execute the selected algorithm." % f)
				return

		# convert input data to the matrix to feed the algorithm
		data = np.array(data)
		inmatrix = DeclusterWdg._toAlgInputData( data[:, indexes] )

		# run the algorithm, then get clusters data
		out_args = self.decluster( inmatrix )
		origdata_clnum, cldata_indexes, cl_info = DeclusterWdg._fromAlgOutputData( *out_args )

		# create the plot dialog
		plot = DeclusteredPlotDlg( parent=None, title="Declustered", labels=("Longitude", "Latitude") )

		# fill the plot using inmatrix instead of data, so long/lat values are 
		# already converted to double
		plot.setData( inmatrix[cldata_indexes, 3], inmatrix[cldata_indexes, 4], info=cl_info[:, 1] )

		return plot

class GardnerKnopoffDeclusterWdg(DeclusterWdg):

	def __init__(self, parent=None):
		DeclusterWdg.__init__(self, parent)
		self.setupUi()
		self.algorithmName = "gardner_knopoff_decluster"

	def setupUi(self):
		layout = QVBoxLayout(self)

		label = QLabel("Time dist window", self)
		layout.addWidget(label)

		self.combo = QComboBox(self)
		self.combo.addItems( ["GardnerKnopoff", "Gruenthal", "Uhrhammer" ] )
		layout.addWidget(self.combo)

		label = QLabel("Foreshock time window", self)
		layout.addWidget(label)

		self.edit = QLineEdit("0.0", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0 )
		self.edit.setValidator( validator )
		layout.addWidget(self.edit)

		self.setLayout(layout)
		return DeclusterWdg.setupUi(self)

	def decluster(self, matrix):
		return self.gardner_knopoff_decluster(matrix)

	def gardner_knopoff_decluster(self, matrix):
		window_opt = unicode(self.combo.currentText())
		fs_time_prop = float(self.edit.text())

		from .mtoolkit.scientific.declustering import gardner_knopoff_decluster
		return gardner_knopoff_decluster(matrix, window_opt, fs_time_prop)


class AfteranDeclusterWdg(DeclusterWdg):

	def __init__(self, parent=None):
		DeclusterWdg.__init__(self, parent)
		self.setupUi()
		self.algorithmName = "afteran_decluster"

	def setupUi(self):
		layout = QVBoxLayout(self)

		label = QLabel("Time dist window", self)
		layout.addWidget(label)

		self.combo = QComboBox(self)
		self.combo.addItems( ["GardnerKnopoff", "Gruenthal", "Uhrhammer" ] )
		layout.addWidget(self.combo)

		label = QLabel("Time window (in days)", self)
		layout.addWidget(label)

		self.edit = QLineEdit("60.0", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0 )
		self.edit.setValidator( validator )
		layout.addWidget(self.edit)

		self.setLayout(layout)
		return DeclusterWdg.setupUi(self)

	def decluster(self, matrix):
		return self.afteran_decluster(matrix)

	def afteran_decluster(self, matrix):
		window_opt = unicode(self.combo.currentText())
		time_window = float(self.edit.text())

		from .mtoolkit.scientific.declustering import afteran_decluster
		return afteran_decluster(matrix, window_opt, time_window)



from plot_wdg import PlotDlg, PlotWdg

class DeclusteredPlotDlg(PlotDlg):
	def createPlot(self, *args, **kwargs):
		return DeclusteredPlotWdg(*args, **kwargs)

class DeclusteredPlotWdg(PlotWdg):
	def _plot(self):
		""" convert query_objectsvalues, then create the plot """

		# set size based on cluster size
		size = self.info	#self.info[:, 0]
		minsize, maxsize = 	np.min(size), np.max(size)+1
		interval = (maxsize - minsize) / 10.0
		# when index is 0 it displays only the events with size equals to minsize
		steps = np.arange(minsize-interval, maxsize+interval, interval)

		for index in range(0, len(steps)-1):
			val, nextval = steps[index], steps[index+1]
			if val < minsize: val = 0

			vsel = np.logical_and(size > val, size <= nextval)
			if any(vsel):
				symb_size = val*5 + 10
				items = self.axes.scatter(self.x[vsel], self.y[vsel], s=symb_size)
				self.collections.append( items )

