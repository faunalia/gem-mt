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

from qgis.core import QGis
from .utils import Utils, LayerStyler

import numpy as np

class DeclusterWdg(QWidget):

	MAP_PLOT, CUMULATIVE_PLOT = range(2)

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self.setupUi()

	def setupUi(self):
		layout = QVBoxLayout(self)
		self.setLayout(layout)

		label = QLabel("Algorithm", self)
		layout.addWidget(label)

		self.algCombo = QComboBox(self)
		self.algCombo.addItems( ["Gardner and Knopoff", "Afteran" ] )
		layout.addWidget(self.algCombo)

		label = QLabel("Window options", self)
		layout.addWidget(label)

		self.winOptCombo = QComboBox(self)
		self.winOptCombo.addItems( ["GardnerKnopoff", "Gruenthal", "Uhrhammer" ] )
		layout.addWidget(self.winOptCombo)

		self.addAlgOptions()
		QObject.connect(self.algCombo, SIGNAL("currentIndexChanged(int)"), self.algorithmChanged)

		spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout.addItem(spacer)

		self.toAsciiBtn = QPushButton("Save to file", self)
		QObject.connect( self.toAsciiBtn, SIGNAL("clicked()"), self.toAscii )
		layout.addWidget(self.toAsciiBtn)

		self.plotMapBtn = QPushButton("Plot map", self)
		QObject.connect( self.plotMapBtn, SIGNAL("clicked()"), self.plotMap )
		layout.addWidget(self.plotMapBtn)

		self.plotDataBtn = QPushButton("Cumulative plot", self)
		QObject.connect( self.plotDataBtn, SIGNAL("clicked()"), self.plotData )
		layout.addWidget(self.plotDataBtn)

		self.loadAsLayerBtn = QPushButton("Add to canvas", self)
		QObject.connect( self.loadAsLayerBtn, SIGNAL("clicked()"), self.loadAsLayer )
		layout.addWidget(self.loadAsLayerBtn)


	def addAlgOptions(self):
		self.stacked = QStackedWidget(self)
		self.layout().addWidget( self.stacked )

		widget = QWidget(self)
		layout = QVBoxLayout(widget)
		self.stacked.addWidget(widget)

		label = QLabel("Foreshock time window", self)
		layout.addWidget(label)

		self.timeWinGardner = QLineEdit("0.0", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0 )
		self.timeWinGardner.setValidator( validator )
		layout.addWidget(self.timeWinGardner)

		widget = QWidget(self)
		layout = QVBoxLayout(widget)
		self.stacked.addWidget(widget)

		label = QLabel("Fixed time window (days)", self)
		layout.addWidget(label)

		self.timeWinAfteran = QLineEdit("60.0", self)
		validator = QDoubleValidator(self)
		validator.setBottom( 0 )
		self.timeWinAfteran.setValidator( validator )
		layout.addWidget(self.timeWinAfteran)

	def timeWinEdit(self):
		if self.algCombo.currentIndex() == 0:
			return self.timeWinGardner
		else:
			return self.timeWinAfteran

	def algorithmChanged(self, index):
		self.stacked.setCurrentIndex( index )
		if index == 0:
			# set GardnerKnopoff as default window option
			self.winOptCombo.setCurrentIndex( 0 )

		elif index == 1:
			# set Uhrhammer as default window option
			self.winOptCombo.setCurrentIndex( 1 )


	def decluster(self, *argv, **kwargs):
		""" This method runs decluster routine on the passed data. """
		if self.algCombo.currentIndex() == 0:
			return self.gardner_knopoff_decluster(*argv, **kwargs)
		else:
			return self.afteran_decluster(*argv, **kwargs)

	def gardner_knopoff_decluster(self, matrix):
		window_opt = unicode(self.winOptCombo.currentText())
		fs_time_prop = float(self.timeWinEdit().text())

		from .mtoolkit.scientific.declustering import gardner_knopoff_decluster
		return gardner_knopoff_decluster(matrix, window_opt, fs_time_prop)

	def afteran_decluster(self, matrix):
		window_opt = unicode(self.winOptCombo.currentText())
		time_window = float(self.timeWinEdit().text())

		from .mtoolkit.scientific.declustering import afteran_decluster
		return afteran_decluster(matrix, window_opt, time_window)


	@staticmethod
	def _fromAlgOutputData(vcl, vmain_shock, flagvector):
		""" convert the list of non-clustered events to a list of information
			used by the plugin.

			returns:
				**vcl** vector indicating cluster number for the input events
				**vncl_idx** indexes of clustered events
				**vcl_info** ndarray with columns containing:
					cluster number, cluster event count """

		vncl_idx = np.flatnonzero(flagvector == 0)	# mainshocks events indexes in vcl
		vcl_num = vcl[vncl_idx]	# cluster number of mainshocks events in vmain_shock 

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
			d = Utils.valueFromQVariant(date)
			return d.year, d.month, d.day

		year, month, day = np.vectorize(toDateParts)(data[:, 3])
		matrix[:, 0] = year.T	# add year
		matrix[:, 1] = month.T	# add month
		matrix[:, 2] = day.T	# add day

		# add longitude, latitude, magnitude
		matrix[:, 3:6] = np.vectorize(lambda x: float(x))(data[:, 0:3])

		return matrix

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
		req = self.requestData( ['longitude','latitude','magnitude','date'] )
		if req is None:
			return
		data, panMap, indexes = req

		# convert input data to the matrix used to feed the algorithm
		inmatrix = DeclusterWdg._toAlgInputData( data[:, indexes] )

		# run the algorithm, then get clusters data
		out_args = self.decluster( inmatrix )
		origdata_clnum, cldata_indexes, cl_info = DeclusterWdg._fromAlgOutputData( *out_args )

		# clusters data: append the cluster info to clustered events matrix
		clusters = np.concatenate( (data[cldata_indexes], cl_info), axis=1 )

		# original data: append the cluster number each the event belongs to
		original = np.concatenate( (data, origdata_clnum.reshape((-1, 1))), axis=1 )

		# create a group containing this routine's output layers
		addGroupFlag = QGis.QGIS_VERSION[0:3] <= '1.8'
		legend = Utils.iface.legendInterface()

		if addGroupFlag:
			# set the events layer as current one to avoid nested groups
			Utils.iface.setActiveLayer( Utils.eventsVl() )
			groupN = legend.addGroup( self.algCombo.currentText() )

		# now create both the original and clusters layers
		layers = {'original' : original, 'clusters' : clusters}
		for name, datamatrix in layers.iteritems():
			# make the layer from scratch, then add it to the canvas
			vl = self._createOutputLayer( name, datamatrix, panMap['longitude'], panMap['latitude'], name == 'original' )
			Utils.addVectorLayer( vl )
			legend.setLayerVisible( vl, name != 'original' )

			# finally put the layer into the group
			if addGroupFlag:
				# XXX the group index is incremented by one because the layer 
				# was added above the group in the legend
				groupN = groupN+1
				legend.moveLayer(vl, groupN)

		if addGroupFlag:
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
		if vl is None:
			return

		# add features
		pr = vl.dataProvider()
		for row in data:
			attrs = dict(enumerate(row[1:].tolist()))
			point = QgsPoint( float(row[longFieldIdx]), row[latFieldIdx].toDouble()[0] )

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
			# we need to scale markers by area
			LayerStyler.setDeclusteredStyle( vl, sizeField )

		return vl


	def plotMap(self):
		self.plot(self.MAP_PLOT)

	def plotData(self):
		self.plot(self.CUMULATIVE_PLOT)

	def plot(self, plotType):
		QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
		try:
			dlg = self._plot(plotType)
			if dlg is None:
				return
		finally:
			QApplication.restoreOverrideCursor()

		# plot clustered data!
		dlg.show()
		dlg.exec_()
		dlg.deleteLater()

	def _plot(self, plotType):
		req = self.requestData( ['longitude','latitude','magnitude','date'] )
		if req is None:
			return
		data, panMap, indexes = req

		# convert input data to the matrix used to feed the algorithm
		inmatrix = DeclusterWdg._toAlgInputData( data[:, indexes] )

		# run the algorithm, then get clusters data
		out_args = self.decluster( inmatrix )
		origdata_clnum, cldata_indexes, cl_info = DeclusterWdg._fromAlgOutputData( *out_args )

		# create the plot dialog
		# fill the plot using inmatrix instead of data, so long/lat values are 
		# already converted to double
		if plotType == self.MAP_PLOT:
			plot = DeclusteredPlotDlg( parent=None, title="Declustered", labels=("Longitude", "Latitude") )
			plot.plotMap( inmatrix[cldata_indexes, 3], inmatrix[cldata_indexes, 4], size=cl_info[:, 1] )
		else:
			# cumulative plot
			plot = DeclusteredPlotDlg( parent=None, title="Declustered", labels=("Time", "Cumulative events") )
			orig_date = np.vectorize(lambda x: Utils.valueFromQVariant(x))(data[:, indexes[3]])
			decl_date = np.vectorize(lambda x: Utils.valueFromQVariant(x))(data[cldata_indexes, indexes[3]])
			plot.plotData( orig_date, decl_date )

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
		filename = QFileDialog.getSaveFileName( self, "Choose where to save the output", "", "ASCII file (*.txt)" )
		if filename == "":
			return

		if filename[-4:] != ".txt":
			filename += ".txt"

		vcl, vmain_shock, flagvector = ret

		with open( unicode(filename), 'w' ) as fout:
			fout.write( "vcl:\n%s" % repr(vcl) )
			fout.write( "\n\nv_mainshock:\n%s" % repr(vmain_shock) )
			fout.write( "\n\nflag_vector:\n%s" % repr(flagvector) )


	def _toAscii(self):
		req = self.requestData( ['longitude','latitude','magnitude','date'] )
		if req is None:
			return
		data, panMap, indexes = req

		# convert input data to the matrix used to feed the algorithm
		inmatrix = DeclusterWdg._toAlgInputData( data[:, indexes] )

		# run the algorithm
		vcl, vmain_shock, flagvector = self.decluster( inmatrix )
		return vcl, vmain_shock, flagvector



from plot_wdg import PlotDlg, PlotWdg

class DeclusteredPlotDlg(PlotDlg):

	def createPlot(self, *args, **kwargs):
		return DeclusteredPlotWdg(*args, **kwargs)

	def plotMap(self, *argv, **kwargs):
		self.plot.plotMap(*argv, **kwargs)

	def plotData(self, *argv, **kwargs):
		self.plot.plotData(*argv, **kwargs)

class DeclusteredPlotWdg(PlotWdg):
	def _plot(self):
		pass

	def plotMap(self, x, y, size):
		""" convert values, then create the plot """

		# marker's size depends on cluster's area
		area_size = np.sqrt( np.array( size ) )

		# compute range_count value to be <= 10
		dist = np.max( area_size ) - np.min( area_size )
		range_count = min( np.ceil(dist), 10 )

		# define min and max sizes
		min_size = 8
		max_size = range_count * 20

		# re-arrange size from min_size to max_size
		marker_size = (area_size-1) / dist * max_size + min_size

		# plot now!
		self.axes.scatter(x, y, s=marker_size)

	def plotData(self, orig, decl):
		""" convert values, then create the plot """
		# plot the original catalog
		n, bins, patches = self._callPlotFunc('hist', orig, color='b', 
											histtype='step', cumulative=True)
		patches[0].set_xy(patches[0].get_xy()[:-1])		# hack! remove the vertical line

		# plot the declustered catalog
		n, bins, patches = self._callPlotFunc('hist', decl, color='k',
											histtype='step', cumulative=True)
		patches[0].set_xy(patches[0].get_xy()[:-1])		# hack! remove the vertical line

		self.axes.set_ylim(bottom=0)

		self.axes.legend(('Original catalog', 'De-clustered catalog'), 
				'upper left', shadow=False, fancybox=False)

