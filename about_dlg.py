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

from ui.DlgAbout_ui import Ui_DlgAbout
import platform
import re
import ConfigParser
import os

try:
	import resources
except ImportError:
	import resources_rc

class AboutDlg(QDialog, Ui_DlgAbout):

	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		self.setupUi(self)
		
		# read parameters from metadata.txt
		config = ConfigParser.ConfigParser()
		config.read( os.path.join( os.path.dirname(__file__), 'metadata.txt' ) )		
		name = config.get("general", "name")
		description = config.get("general", "description")
		version = config.get("general", "version")
		
		self.logo.setPixmap( QPixmap( ":/faunalia/logo" ) )
		self.title.setText( name )
		self.description.setText( description )

		text = self.txt.toHtml()
		text = re.sub("\$PLUGIN_NAME\$", name, text)

		subject = "Help: %s" % name
		body = """\n\n
--------
Plugin name: %s
Plugin version: %s
Python version: %s
Platform: %s - %s
--------
""" % ( name, version, platform.python_version(), platform.system(), platform.version() )

		mail = QUrl( "mailto:abc@abc.com" )
		mail.addQueryItem( "subject", subject )
		mail.addQueryItem( "body", body )

		text = re.sub("$MAIL_SUBJECT$", unicode(mail.encodedQueryItemValue( "subject" )), text)
		text = re.sub("$MAIL_BODY$", unicode(mail.encodedQueryItemValue( "body" )), text)

		self.txt.setHtml(text)


