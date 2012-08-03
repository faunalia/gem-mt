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

def name():
	return "GEM Modellers Toolkit plugin"

def description():
	return "Analysing and Processing Earthquake Catalogue Data"

def authorName():
	return "Giuseppe Sucameli (Faunalia)"

def icon():
	return "icons/logo.png"

def version():
	return "0.0.5"

def qgisMinimumVersion():
	return "1.5"

def classFactory(iface):
	from gem_mt_plugin import GEM_MT_Plugin
	return GEM_MT_Plugin(iface)

