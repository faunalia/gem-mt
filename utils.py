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

from qgis.core import QgsMapLayerRegistry
from qgis.core import QgsSymbolV2, QgsGraduatedSymbolRendererV2, QgsRendererRangeV2

import qgis.utils

class Utils:

	@staticmethod
	def addVectorLayer(vl):
		# add the new layer to the map
		if hasattr(QgsMapLayerRegistry.instance(), 'addMapLayers'):	# available from QGis >= 1.8
			QgsMapLayerRegistry.instance().addMapLayers( [ vl ] )
		else:
			QgsMapLayerRegistry.instance().addMapLayer( vl )


	@staticmethod
	def key2indexFieldMap( fields ):
		key2index = {}

		for index, fld in fields.iteritems():
			key = Utils.fieldName2key( fld.name() )
			if key:
				key2index[ key ] = index

		return key2index

	@staticmethod
	def index2keyFieldMap( fields ):
		index2key = {}

		for index, fld in fields.iteritems():
			key = Utils.fieldName2key( fld.name() )
			if key:
				index2key[ index ] = key

		return index2key

	@staticmethod
	def fieldName2key( fieldName ):
		from settings_dlg import Settings

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

	@staticmethod
	def colorGenerator(col1, col2, count):
		rdiff, gdiff, bdiff = col2.red()-col1.red(), col2.green()-col1.green(), col2.blue()-col1.blue()
		for i in range(count):
			step = i/float(count-1)
			rstep, gstep, bstep = int(rdiff*step), int(gdiff*step), int(bdiff*step)
			yield QColor(col1.red()+rstep, col1.green()+gstep, col1.blue()+bstep)


class LayerStyler:

	@staticmethod
	def setBasemapStyle(vl):
		# set the basemap layer color
		if not vl.isUsingRendererV2():
			vl.setRendererV2(QgsSingleSymbolRendererV2())
		vl.rendererV2().symbol().setColor( QColor( "#FFF1B7" ) )	# beige

	@staticmethod
	def setEarthquakesStyle(vl):
		# get involved fields to set layer style
		pr = vl.dataProvider()
		fields = pr.fields()
		key2indexFieldMap = Utils.key2indexFieldMap( fields )

		depthFieldIndex = key2indexFieldMap.get('depth', None)
		if depthFieldIndex:
			depthFieldName = fields[depthFieldIndex].name()
			minDepth, minOk = pr.minimumValue( depthFieldIndex ).toDouble()
			maxDepth, maxOk = pr.maximumValue( depthFieldIndex ).toDouble()

			if minOk and maxOk:
				# define value ranges which raise esponentially up
				minVal = int(minDepth) if minDepth >= 0 else 0
				count = 6
				stepCount = reduce(lambda x,y: x+y, [2**i for i in range(count)])	# 1+2+4+8+16+32
				stepSize = float(maxDepth - minVal) / stepCount

				ranges = []
				for i in range(count):
					step = int(stepSize * (2**i))
					values = (lastVal, lastVal + step) if i > 0 else (minDepth, minVal + step)
					ranges.append( values )
					lastVal = values[1]

				# create a color generator red->yellow
				colors = Utils.colorGenerator(QColor("red"), QColor("yellow"), len(ranges))

				# create all the ranges
				rangeV2List = []
				for i, color in enumerate(colors):
					min_val, max_val = ranges[i]

					# make our symbol and range...
					if i == 0:
						label = 'depth <= %s' % max_val
					elif i == len(ranges)-1:
						label = 'depth > %s' % min_val
					else:
						label = '%s < depth <= %s' % (min_val, max_val)
			
					symbolV2 = QgsSymbolV2.defaultSymbol( vl.geometryType() )
					symbolV2.setColor(color)
					symbolV2.setSize(0.8)
					rangeV2 = QgsRendererRangeV2(min_val, max_val, symbolV2, label)
					rangeV2List.append(rangeV2)

				# create the renderer
				renderer = QgsGraduatedSymbolRendererV2( depthFieldName, rangeV2List )

				# set magnitude as size scale field
				magnitudeFieldIndex = key2indexFieldMap.get('magnitude', None)
				if magnitudeFieldIndex:
					magnitudeFieldName = fields[magnitudeFieldIndex].name()
					renderer.setSizeScaleField( magnitudeFieldName )

				# set the renderer for the layer
				vl.setRendererV2( renderer )
				qgis.utils.iface.legendInterface().refreshLayerSymbology(vl)

	@staticmethod
	def setClassifiedStyle(vl):
		# set a categorized style
		from qgis.core import QgsSymbolV2, QgsCategorizedSymbolRendererV2, QgsRendererCategoryV2

		categories = [
			("shallow", "shallow", QColor("red")),	# shallow earthquakes in red
			("deep", "deep", QColor("blue"))	# deep earthquakes in blue
		]

		# create a category for each class
		categoryV2List = []
		for label, value, color in categories:
			symbolV2 = QgsSymbolV2.defaultSymbol( vl.geometryType() )
			symbolV2.setColor( color )
			symbolV2.setSize(0.8)
			categoryV2 = QgsRendererCategoryV2( value, symbolV2, label )
			categoryV2List.append( categoryV2 )

		# create the renderer
		renderer = QgsCategorizedSymbolRendererV2( "classType", categoryV2List )

		# set magnitude as size scale field
		fields = vl.dataProvider().fields()
		key2indexFieldMap = Utils.key2indexFieldMap( fields )
		magnitudeFieldIndex = key2indexFieldMap.get('magnitude', None)
		if magnitudeFieldIndex:
			magnitudeFieldName = fields[magnitudeFieldIndex].name()
			renderer.setSizeScaleField( magnitudeFieldName )

		# set the renderer for the layer
		vl.setRendererV2( renderer )

