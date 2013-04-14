# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : GEM Modellers Toolkit plugin (GEM-MT)
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
	return "EQCAP - EarthQuake Catalogue Analysis Plugin"

def description():
	return "Analysing and Processing Earthquake Catalogue Data"

def authorName():
	return author()

def author():
	return "Giuseppe Sucameli (Faunalia)"

def email():
	return "sucameli@faunalia.it"

def icon():
	return "icons/logo.png"

def version():
	return "1.0.1"

def qgisMinimumVersion():
	return "1.5"

def classFactory(iface):
	from gem_mt_plugin import GEM_MT_Plugin
	return GEM_MT_Plugin(iface)

