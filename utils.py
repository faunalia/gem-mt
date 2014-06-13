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

from qgis.core import QGis, QgsMapLayerRegistry, QgsVectorLayer, QgsGeometry

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
			elif fld.type() == 'int':
				return "integer"
			elif fld.type() == "float":
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

		for fld in fields.toList():
			key = Utils.fieldName2key( fld.name() )
			if key:
				key2index[ key ] = fields.indexFromName(fld.name())

		return key2index

	@staticmethod
	def index2keyFieldMap( fields ):
		index2key = {}

		for fld in fields.toList():
			key = Utils.fieldName2key( fld.name() )
			if key:
				index2key[ fields.indexFromName(fld.name()) ] = key

		return index2key

	@staticmethod
	def fieldName2key( fieldName ):
		from settings_dlg import Settings
		
		if not Settings.longitudeField() == "" and \
				fieldName.lower().startswith( Settings.longitudeField().lower() ):
			return 'longitude'
		if not Settings.latitudeField() == "" and \
				fieldName.lower().startswith( Settings.latitudeField().lower() ):
			return 'latitude'
		if not Settings.magnitudeField() == "" and \
				fieldName.lower().startswith( Settings.magnitudeField().lower() ):
			return 'magnitude'
		if not Settings.depthField() == "" and \
				fieldName.lower().startswith( Settings.depthField().lower() ):
			return 'depth'
		if not Settings.dateField() == "" and \
				fieldName.lower().startswith( Settings.dateField().lower() ):
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
# 		if not isinstance(val, QVariant):
# 			return val

		if isinstance(val, int):
			return val
		elif isinstance(val, float):
			return val
		elif type(val) == QVariant.Date:
			return val.toDate().toPyDate()
		elif type(val) == QVariant.DateTime:
			return val.toDateTime().toPyDateTime()

		# try to convert the value to a date
		from datetime import datetime
		s = unicode(val)
		try:
			return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
		except ValueError:
			pass
		try:
			return datetime.strptime(s, '%Y-%m-%d')
		except ValueError:
			pass
		
		try:
			v = float(val)
			return v
		except:
			pass
		try:
			v = int(val)
			return v
		except:
			pass
		try:
			v = val.toDateTime().toPyDateTime()
			return v
		except:
			pass
		try:
			v = val.toDate().toPyDate()
			return v
		except:
			pass

		return unicode(s)

	@staticmethod
	def distanceAlongProfile(line, point):
		""" Calculate the distance of the point along the profile.

		    It uses the pythagorean theorem to get the distance.
		    It's really approximated (since ellipsoid is not considered at 
		    all) but distances are in a small range (~200m). """
		import math
		cat1 = line.distance( point )
		start_point = QgsGeometry.fromPoint( line.vertexAt( 0 ) )
		hip = start_point.distance( point )
		return math.sqrt( hip*hip - cat1*cat1 )



import math
from qgis.core import QgsSymbolV2, QgsSingleSymbolRendererV2
from qgis.core import QgsGraduatedSymbolRendererV2, QgsRendererRangeV2
from qgis.core import QgsCategorizedSymbolRendererV2, QgsRendererCategoryV2

class LayerStyler:

	@staticmethod
	def setBasemapStyle(vl):
		# set the basemap layer color
		vl.setRendererV2(QgsSingleSymbolRendererV2( QgsSymbolV2.defaultSymbol(vl.geometryType()) ))
		vl.rendererV2().symbol().setColor( QColor( "#FFF1B7" ) )	# beige

	@staticmethod
	def setGraduatedStyle(vl, ranges, field, **kwargs):
		""" set a graduated style """
		# make a symbol for each range
		rangeV2List = []
		for min_val, max_val, attrs in ranges:
			if 'label' in attrs:
				label = attrs['label']
			#elif min_val == None:
			#	label = u'%s <= %s' % (field, max_val)
			#elif max_val == None:
			#	label = u'%s > %s' % (field, min_val)
			else:
				label = u'%s < %s <= %s' % (min_val, field, max_val)
	
			symbolV2 = QgsSymbolV2.defaultSymbol( vl.geometryType() )
			if 'color' in attrs:
				symbolV2.setColor( attrs['color'] )
			if 'size' in attrs:
				symbolV2.setSize( attrs['size'] )

			# from QGis > 1.8 QgsMarkerSymbolV2 has 2 scale methods: ScaleArea and ScaleDiameter
			if 'sizeScaleMethod' in kwargs and hasattr(symbolV2, 'setScaleMethod'):
				symbolV2.setScaleMethod( kwargs['sizeScaleMethod'] )

			rangeV2 = QgsRendererRangeV2(min_val, max_val, symbolV2, label)
			rangeV2List.append(rangeV2)

		# create the renderer
		renderer = QgsGraduatedSymbolRendererV2( field, rangeV2List )

		# set size scale field
		if 'sizeScaleField' in kwargs:
			renderer.setSizeScaleField( kwargs['sizeScaleField'] )

		# set the renderer for the layer
		vl.setRendererV2( renderer )
		Utils.iface.legendInterface().refreshLayerSymbology(vl)

	@staticmethod
	def setDeclusteredStyle(vl, sizeField):
		color = QColor('blue')

		# in QGis > 1.8 QgsMarkerSymbolV2 has 2 size scale methods: ScaleArea and ScaleDiameter.
		# Let's use ScaleArea with a single symbol renderer!
		if hasattr(QgsSymbolV2, 'ScaleArea'):
			Utils.setSimpleStyle( vl, color=color, size=1.0, sizeScaleField=sizeField, sizeScaleMethod=QgsSymbolV2.ScaleArea )
			return

		# in QGis <= 1.8 we have to use a graduated renderer with 
		# proper ranges to emulate ScaleArea size scale method.
		if vl.featureCount() == 0:
			return	# cannot calcolate ranges values

		# get involved fields to set layer style
		pr = vl.dataProvider()
		index = pr.fieldNameIndex( sizeField )
		if index is None or index < 0:
			return

		# let's reset the subset string to get real min/max
		pr.setSubsetString("")
		try:
			minVal = float( pr.minimumValue( index ) )
			maxVal = float( pr.maximumValue( index ) )
		except:
			return

		minVal = math.floor(minVal)
		maxVal = math.ceil(maxVal)

		count = min(6, maxVal-minVal)	# how many ranges?

		# calculate the step size
		steps = [i+1 for i in range(count)]	# 1,2,3,4,5,6,...
		stepSize = float(maxVal - minVal) / sum(steps)

		# define the ranges
		ranges = []
		for i in range(count):
			step = stepSize * steps[i]
			if i == 0:
				values = (minVal, minVal + step)
			elif i == count-1:
				values = (lastVal, maxVal)
			else:
				values = (lastVal, lastVal + step)
			ranges.append( (int(values[0]), int(values[1]), {'color':color, 'size':1+i} ) )
			lastVal = values[1]

		# set the layer style
		LayerStyler.setGraduatedStyle( vl, ranges, sizeField )
		

	@staticmethod
	def setEarthquakesStyle(vl):
		if vl.featureCount() == 0:
			return	# cannot calcolate ranges values

		# get involved fields to set layer style
		pr = vl.dataProvider()
		fields = pr.fields()
		key2index = Utils.key2indexFieldMap( fields )

		depthFieldIndex = key2index.get('depth', None)
		if depthFieldIndex is None:
			return
		depthFieldName = fields[ depthFieldIndex ].name()

		# let's reset the subset string to get real min/max
		pr.setSubsetString("")
		try:
			minDepth = float( pr.minimumValue( depthFieldIndex ) )
			maxDepth = float( pr.maximumValue( depthFieldIndex ) )
		except:
			return
		
		minVal = math.floor(minDepth)
		maxVal = math.ceil(maxDepth)

		# define value ranges which raise esponentially up
		# how many ranges?
		count = 1
		# TODO: use log2() instead
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
			step = stepSize * steps[i]
			if i == 0:
				values = (minVal, minVal + step)
			elif i == count-1:
				values = (lastVal, maxVal)
			else:
				values = (lastVal, lastVal + step)
			ranges.append( ( int(values[0]), int(values[1]), {'color':col, 'size':1.5} ) )
			lastVal = values[1]

		# put advanced rendering options into the props dictionary
		props = {}

		# if magnitude field is not found markers wont be scaled
		try:
			magnFieldIdx = key2index['magnitude']
			props['sizeScaleField'] = fields[ magnFieldIdx ].name()

			# ScaleDiameter scale method is not present in QGis <= 1.8
			if hasattr(QgsSymbolV2, 'ScaleDiameter'):
				props['sizeScaleMethod'] = QgsSymbolV2.ScaleDiameter
				#props['sizeScaleMethod'] = QgsSymbolV2.ScaleArea
		except KeyError:
			pass


		# set the layer style
		LayerStyler.setGraduatedStyle( vl, ranges, depthFieldName, **props )


	@staticmethod
	def setCategorizedStyle(vl, categories, field, **kwargs):
		""" set a categorized style """
		# make a symbol for each category
		categoryV2List = []
		for label, value, attrs in categories:
			symbolV2 = QgsSymbolV2.defaultSymbol( vl.geometryType() )
			if 'color' in attrs:
				symbolV2.setColor( attrs['color'] )
			if 'size' in attrs:
				symbolV2.setSize( attrs['size'] )

			# in QGis > 1.8 QgsMarkerSymbolV2 has 2 scale methods: ScaleArea and ScaleDiameter
			if 'sizeScaleMethod' in kwargs and hasattr(symbolV2, 'setScaleMethod'):
				symbolV2.setScaleMethod( kwargs['sizeScaleMethod'] )

			categoryV2 = QgsRendererCategoryV2( value, symbolV2, label )
			categoryV2List.append( categoryV2 )

		# create the renderer
		renderer = QgsCategorizedSymbolRendererV2( field, categoryV2List )

		# set size scale field
		if 'sizeScaleField' in kwargs:
			renderer.setSizeScaleField( kwargs['sizeScaleField'] )

		# set the renderer for the layer
		vl.setRendererV2( renderer )
		Utils.iface.legendInterface().refreshLayerSymbology(vl)

	@staticmethod
	def setClassifiedStyle(vl, field, size=1.0):
		# create categories
		categories = [
			("shallow", "shallow", {'color':QColor("red"), 'size':size}),	# shallow earthquakes in red
			("deep", "deep", {'color':QColor("blue"), 'size':size})	# deep earthquakes in blue
		]

		# put advanced rendering options into the props dictionary
		props = {}

		# if magnitude field is not found markers wont be scaled
		fields = vl.dataProvider().fields()
		try:
			magnFieldIdx = Utils.key2indexFieldMap( fields )['magnitude']
			props['sizeScaleField'] = fields[ magnFieldIdx ].name()

			# ScaleDiameter scale method is not present in QGis <= 1.8
			if hasattr(QgsSymbolV2, 'ScaleDiameter'):
				props['sizeScaleMethod'] = QgsSymbolV2.ScaleDiameter
		except KeyError:
			pass

		# set the layer style
		LayerStyler.setCategorizedStyle( vl, categories, field, **props )

	@staticmethod
	def setSimpleStyle(vl, **kwargs):
		""" set a simple style """
		symbolV2 = QgsSymbolV2.defaultSymbol( vl.geometryType() )
		if 'color' in kwargs:
			symbolV2.setColor( kwargs['color'] )
		size = kwargs.get('size', None)
		if 'size' in kwargs:
			symbolV2.setSize( kwargs['size'] )

		# in QGis > 1.8 QgsMarkerSymbolV2 has 2 scale methods: ScaleArea and ScaleDiameter
		if 'sizeScaleMethod' in kwargs and hasattr(symbolV2, 'setScaleMethod'):
			symbolV2.setScaleMethod( kwargs['sizeScaleMethod'] )

		# create the renderer
		renderer = QgsSingleSymbolRendererV2( symbolV2 )

		# set size scale field
		if 'sizeScaleField' in kwargs:
			renderer.setSizeScaleField( kwargs['sizeScaleField'] )

		# set the renderer for the layer
		vl.setRendererV2( renderer )
		Utils.iface.legendInterface().refreshLayerSymbology(vl)

