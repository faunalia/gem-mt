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

from qgis.core import QGis, QgsMapLayerRegistry, QgsVectorLayer

import qgis.utils

class Utils:

	iface = qgis.utils.iface

	@staticmethod
	def eventsVl():
		from gem_mt_plugin import GEM_MT_Plugin
		return GEM_MT_Plugin.instance.eventsLayer()

	@staticmethod
	def basemapVl():
		from gem_mt_plugin import GEM_MT_Plugin
		return GEM_MT_Plugin.instance.basemapLayer()

	@staticmethod
	def classifiedVl():
		from gem_mt_plugin import GEM_MT_Plugin
		return GEM_MT_Plugin.instance.classifiedLayer()


	@staticmethod
	def addVectorLayer(vl):
		if QgsMapLayerRegistry.instance().mapLayer( vl.id() ):
			return	# already added

		# add the new layer to the map
		if hasattr(QgsMapLayerRegistry.instance(), 'addMapLayers'):	# available from QGis >= 1.8
			QgsMapLayerRegistry.instance().addMapLayers( [ vl ] )
		else:
			QgsMapLayerRegistry.instance().addMapLayer( vl )

	@staticmethod
	def createMemoryLayer(geomtype, crs, fields, name):
		def memoryTypeName(fld):
			if fld.type() == QVariant.Int:
				return "integer"
			elif fld.type() == QVariant.Double:
				return "double"
			return "string"

		# create the output layer
		uri = u"%s?crs=%s" % (geomtype, crs)
		for fld in fields:
			uri += u"&field=%s:%s" % (fld.name(), memoryTypeName(fld))

		vl = QgsVectorLayer(uri, name, "memory")
		if not vl.isValid():
			return

		return vl

	@staticmethod
	def getItemLegendPosition( itemName ):
		legend = Utils.iface.legendInterface()
		for index, (group, layers) in enumerate(legend.groupLayerRelationship()):
			if group == "" and layers[0] == itemName:	# it contains 1 top-level layer
				return index
			if group == itemName:
				return index
		return -1


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

	@staticmethod
	def toDisplayedSize(size):
		# convet to Km/Kft/degrees
		if Utils.iface.mapCanvas().mapUnits() in [QGis.Meters, QGis.Feet]:
			return size / 1000.0
		return size

	@staticmethod
	def fromDisplayedSize(size):
		# convet back to m/ft/degrees
		if Utils.iface.mapCanvas().mapUnits() in [QGis.Meters, QGis.Feet]:
			return size * 1000.0
		return size


	@staticmethod
	def valueFromQVariant(val):
		""" function to convert values to proper types """
		if not isinstance(val, QVariant):
			return val

		if val.type() == QVariant.Int:
			return val.toInt()[0]
		elif val.type() == QVariant.Double:
			return val.toDouble()[0]
		elif val.type() == QVariant.Date:
			return val.toDate().toPyDate()
		elif val.type() == QVariant.DateTime:
			return val.toDateTime().toPyDateTime()

		# try to convert the value to a date
		from datetime import datetime
		s = unicode(val.toString())
		try:
			return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
		except ValueError:
			pass
		try:
			return datetime.strptime(s, '%Y-%m-%d')
		except ValueError:
			pass

		v, ok = val.toDouble()
		if ok: return v
		v, ok = val.toInt()
		if ok: return v
		v = val.toDateTime()
		if v.isValid(): return v.toPyDateTime()
		v = val.toDate()
		if v.isValid(): return v.toPyDate()

		return unicode(s)



class LayerStyler:

	@staticmethod
	def setBasemapStyle(vl):
		# set the basemap layer color
		if not vl.isUsingRendererV2():
			vl.setRendererV2(QgsSingleSymbolRendererV2())
		vl.rendererV2().symbol().setColor( QColor( "#FFF1B7" ) )	# beige

	@staticmethod
	def setGraduatedStyle(vl, ranges, field, **kwargs):
		""" set a graduated style """
		from qgis.core import QgsSymbolV2, QgsGraduatedSymbolRendererV2, QgsRendererRangeV2

		# make a symbol for each range
		rangeV2List = []
		for min_val, max_val, attrs in ranges:
			if attrs.has_key('label'):
				label = attrs['label']
			#elif min_val == None:
			#	label = u'%s <= %s' % (field, max_val)
			#elif max_val == None:
			#	label = u'%s > %s' % (field, min_val)
			else:
				label = u'%s < %s <= %s' % (min_val, field, max_val)
	
			symbolV2 = QgsSymbolV2.defaultSymbol( vl.geometryType() )
			col = attrs.get('color', None)
			if col is not None:
				symbolV2.setColor( col )
			size = attrs.get('size', None)
			if size is not None:
				symbolV2.setSize( size )
			rangeV2 = QgsRendererRangeV2(min_val, max_val, symbolV2, label)
			rangeV2List.append(rangeV2)

		# create the renderer
		renderer = QgsGraduatedSymbolRendererV2( field, rangeV2List )

		# set size scale field
		sizeScaleField = kwargs.get('sizeScaleField', None)
		if sizeScaleField:
			renderer.setSizeScaleField( sizeScaleField )

		# set the renderer for the layer
		vl.setRendererV2( renderer )
		Utils.iface.legendInterface().refreshLayerSymbology(vl)

	@staticmethod
	def setDeclusteredStyle(vl, sizeField):
		if vl.featureCount() == 0:
			return	# cannot calcolate ranges values

		# get involved fields to set layer style
		pr = vl.dataProvider()
		index = pr.fieldNameIndex( sizeField )
		if index is None or index < 0:
			return

		# let's reset the subset string to get real min/max
		pr.setSubsetString("")
		minVal, minOk = pr.minimumValue( index ).toDouble()
		maxVal, maxOk = pr.maximumValue( index ).toDouble()

		if not minOk or not maxOk:
			return

		minVal = int(minVal) - 1
		maxVal = int(maxVal) + 1

		# compute value ranges
		count = min(6, maxVal-minVal)	# how many ranges?
		step = int(float(maxVal - minVal) / count)	# step size
		ticks = range(minVal, maxVal+step, step)
		ranges = []
		for i in range(count):
			ranges.append( (ticks[i], ticks[i+1], {'color':QColor('blue'), 'size':1+i} ) )

		# set the layer style
		LayerStyler.setGraduatedStyle( vl, ranges, sizeField )
		

	@staticmethod
	def setEarthquakesStyle(vl):
		if vl.featureCount() == 0:
			return	# cannot calcolate ranges values

		# get involved fields to set layer style
		pr = vl.dataProvider()
		fields = pr.fields()
		key2indexFieldMap = Utils.key2indexFieldMap( fields )

		depthFieldIndex = key2indexFieldMap.get('depth', None)
		if depthFieldIndex is None:
			return

		depthFieldName = fields[depthFieldIndex].name()

		# let's reset the subset string to get real min/max
		pr.setSubsetString("")
		minDepth, minOk = pr.minimumValue( depthFieldIndex ).toDouble()
		maxDepth, maxOk = pr.maximumValue( depthFieldIndex ).toDouble()

		if not minOk or not maxOk:
			return

		minVal = int(minDepth) - 1
		maxVal = int(maxDepth) + 1

		# define value ranges which raise esponentially up
		# how many ranges?
		count = 1
		while 2**count < maxVal - minVal:
			count += 1
		count = min(6, count)

		# create a color generator red->yellow
		colors = Utils.colorGenerator(QColor("red"), QColor("yellow"), count)

		# calculate the step size
		steps = [2**i for i in range(count)]	# 1,2,4,8,16,32,...
		stepSize = float(maxVal - minVal) / sum(steps)

		# define the ranges
		ranges = []
		for i, col in enumerate(colors):
			step = int(stepSize * steps[i])
			if i == 0:
				values = (minVal, minVal + step)
			elif i == count-1:
				values = (lastVal, maxVal)
			else:
				values = (lastVal, lastVal + step)
			ranges.append( (values[0], values[1], {'color':col, 'size':0.8} ) )
			lastVal = values[1]

		# put advanced rendering options into the props dictionary
		props = {}

		magnitudeFieldIndex = key2indexFieldMap.get('magnitude', None)
		if magnitudeFieldIndex is not None:
			props['sizeScaleField'] = fields[magnitudeFieldIndex].name()

		# set the layer style
		LayerStyler.setGraduatedStyle( vl, ranges, depthFieldName, **props )


	@staticmethod
	def setCategorizedStyle(vl, categories, field, **kwargs):
		""" set a categorized style """
		from qgis.core import QgsSymbolV2, QgsCategorizedSymbolRendererV2, QgsRendererCategoryV2

		# make a symbol for each category
		categoryV2List = []
		for label, value, attrs in categories:
			symbolV2 = QgsSymbolV2.defaultSymbol( vl.geometryType() )
			col = attrs.get('color', None)
			if col is not None:
				symbolV2.setColor( col )
			size = attrs.get('size', None)
			if size is not None:
				symbolV2.setSize( size )

			if hasattr(symbolV2, 'setScaleMethod'):
				# from QGis > 1.8 QgsSymbolV2 has 2 scale methods:
				# ScaleArea (default) and ScaleDiameter
				symbolV2.setScaleMethod( QgsSymbolV2.ScaleDiameter )

			categoryV2 = QgsRendererCategoryV2( value, symbolV2, label )
			categoryV2List.append( categoryV2 )

		# create the renderer
		renderer = QgsCategorizedSymbolRendererV2( field, categoryV2List )

		# set size scale field
		sizeScaleField = kwargs.get('sizeScaleField', None)
		if sizeScaleField:
			renderer.setSizeScaleField( sizeScaleField )

		# set the renderer for the layer
		vl.setRendererV2( renderer )
		Utils.iface.legendInterface().refreshLayerSymbology(vl)

	@staticmethod
	def setClassifiedStyle(vl, field, size=1.0, sizeScaleField=None):
		fields = vl.dataProvider().fields()
		key2indexFieldMap = Utils.key2indexFieldMap( fields )

		# create categories
		categories = [
			("shallow", "shallow", {'color':QColor("red"), 'size':size}),	# shallow earthquakes in red
			("deep", "deep", {'color':QColor("blue"), 'size':size})	# deep earthquakes in blue
		]

		# put advanced rendering options into the props dictionary
		props = {}

		if sizeScaleField is None:
			sizeScaleFieldIndex = key2indexFieldMap.get('magnitude', None)
		elif isinstance(sizeScaleField, int):
			sizeScaleFieldIndex = sizeScaleField
		else:
			for index, fld in fields.iteritems():
				if fld.name() == sizeScaleField:
					sizeScaleFieldIndex = index
					break

		if sizeScaleFieldIndex is not None:
			props['sizeScaleField'] = fields[sizeScaleFieldIndex].name()

		# set the layer style
		LayerStyler.setCategorizedStyle( vl, categories, field, **props )

	@staticmethod
	def setSimpleStyle(vl, **kwargs):
		""" set a simple style """
		from qgis.core import QgsSymbolV2, QgsSingleSymbolRendererV2

		symbolV2 = QgsSymbolV2.defaultSymbol( vl.geometryType() )
		col = kwargs.get('color', None)
		if col is not None:
			symbolV2.setColor( col )
		size = kwargs.get('size', None)
		if size is not None:
			symbolV2.setSize( size )

		# create the renderer
		renderer = QgsSingleSymbolRendererV2( symbolV2 )

		# set size scale field
		sizeScaleField = kwargs.get('sizeScaleField', None)
		if sizeScaleField:
			renderer.setSizeScaleField( sizeScaleField )

		# set the renderer for the layer
		vl.setRendererV2( renderer )
		Utils.iface.legendInterface().refreshLayerSymbology(vl)

