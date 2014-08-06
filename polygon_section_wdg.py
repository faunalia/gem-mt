# -*- coding: utf-8 -*-

"""
/****************************************************************************
Name			 	: GEM Modellers Toolkit plugin (GEM-MT)
Description			: Analysing and Processing Earthquake Catalogue Data
Date				: Jun 21, 2012 
copyright			: (C) 2012 by Giuseppe Sucameli (Faunalia)
email				: brush.tyler@gmail.com
 ****************************************************************************/

/****************************************************************************
 *																			*
 *	This program is free software; you can redistribute it and/or modify	*
 *	it under the terms of the GNU General Public License as published by	*
 *	the Free Software Foundation; either version 2 of the License, or		*
 *	(at your option) any later version.										*
 *																			*
 ****************************************************************************/
"""

from PyQt4 import QtGui, QtCore
from .utils import Utils

from .plot_wdg import PlotDlg, PlotWdg, NavigationToolbar
from .classification_wdg import ClassesTableModel
import resources_rc

import matplotlib.pyplot as plt
import numpy as np

class PolygonSectionDlg(PlotDlg):

	def __init__(self, classificationMap, parent=None, classModel=None):
		self._classificationMap = classificationMap

		PlotDlg.__init__(self, parent=parent)
		self.connect(self.nav, QtCore.SIGNAL("classificationUpdateRequested"), self.updateClassification)

		# add lateral toolbar with list of classes and buttons
		self.toolbar = ClassesToolbar( self )
		self.hLayout.insertWidget( 0, self.toolbar )
				
		# get model from class table widget of the parent classification 
		if classModel:
# 			model = ClassificationTableModel(self) # new model based on the classModel adding some infos
# 			model.setSourceModel(classModel)
# 			model.setHeaderData(0, QtCore.Qt.Horizontal, "Class name" )
# 			model.setHeaderData(1, QtCore.Qt.Horizontal, "Drawn" )
			self.toolbar.classesTable.setModel(classModel)

	def createPlot(self):
		return PolygonSectionGraph( self._classificationMap )

	def createToolBar(self):
		return NavigationToolbarPolygonSection(self.plot, self)


	def closeEvent(self, event):
		self.updateClassification()
		return QtGui.QDialog.closeEvent(self, event)

		
	def updateClassification(self):
		self.emit( QtCore.SIGNAL("classificationUpdateRequested") )

	def classify(self):
# 		path = self.plot.polygon.get_path()
# 		
# 		# classify earthquakes and discard indeterminate ones 
# 		shallow, deep = [], []
# 		for index in range(len(self.plot.x)):
# 			point = self.plot.itemAt(index)
# 			if not point:
# 				continue
# 
# 			px, py = point
# 			info = self.plot.info[index]
# 			
# 			# check if point is in polygon
# 			if self.plot.polygon.contains_point(point);
# 			if py > hy:
# 				shallow.append( info )
# 			elif ocoeff == None:
# 				if px <= ox0:
# 					deep.append( info )
# 			else:
# 				y = ocoeff * (px - ox0) + oy0
# 				if py <= y:
# 					deep.append( info )
		
		shallow, deep = [], []
		return (shallow, deep)


from .ui.crosssection_classes_toolbar_ui import Ui_crossSectionClassesToolbar

class ClassesToolbar(QtGui.QWidget, Ui_crossSectionClassesToolbar):
	"""
	Class to add ClassesList and buttons to draw or remove poligon from the plot
	"""
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		Ui_crossSectionClassesToolbar.__init__(self)
		
		self.canvas = parent.plot
		self.dlg = parent
		self.setupUi(self)

		self._idPress = None
		self._idRelease = None
		self._idMotion = None
		self.currentClassName = None
		self.drawButton.clicked.connect(self.drawPolygon)
		self.removeButton.clicked.connect(self.removePolygon)
		
		# data model to contain polygon and labels
		# will be a dictionary as:
		# self.drawnClasses[self.currentClassName] = {"polygon":plt.polygon, "label":plt.text}
		self.drawnClasses = {}

	def removePolygon(self):
		# check if a class is selected
		indexes = self.dlg.toolbar.classesTable.selectedIndexes()
		if len(indexes) != 1:
			return
		index = indexes[0]
		
		self.currentClassName = index.model().getClassName( index )
		if self.currentClassName in self.drawnClasses:
			print "remove", self.currentClassName
			self.drawnClasses[self.currentClassName]["polygon"].remove()
			self.drawnClasses[self.currentClassName]["polygon"].set_visible(False)
			if self.drawnClasses[self.currentClassName]["label"]:
				self.drawnClasses[self.currentClassName]["label"].remove()
				self.drawnClasses[self.currentClassName]["label"].set_visible(False)
			self.drawnClasses.pop(self.currentClassName)
			self.canvas.draw()

	def drawPolygon(self):
		if not self.drawButton.isChecked():
			self.stopMouseCapture()
			self._active = None
			self.mode = ''
			self.dlg.nav.set_message(self.mode)
			return

		# check if a class is selected
		self.currentClassName = None
		indexes = self.dlg.toolbar.classesTable.selectedIndexes()
		if len(indexes) != 1:
			self.drawButton.setChecked(False)
			return
		index = indexes[0]
		self.currentClassName = index.model().getClassName( index )
		print self.currentClassName
		
		# init polygon data
		if self.currentClassName in self.drawnClasses:
			self.drawnClasses[self.currentClassName]["polygon"].remove()
			self.drawnClasses[self.currentClassName]["polygon"].set_visible(False)
			if self.drawnClasses[self.currentClassName]["label"]:
				self.drawnClasses[self.currentClassName]["label"].remove()
				self.drawnClasses[self.currentClassName]["label"].set_visible(False)
			self.drawnClasses.pop(self.currentClassName)
			
		self.vertices = []
		
		self.startMouseCapture()

		self._active = 'POLYGON'
		self.mode = 'draw polygon'
		self.dlg.nav.set_message(self.mode)

	def startMouseCapture(self):
		# remove old handlers
		self.stopMouseCapture()

		# set new handlers
		if not self._idPress:
			self._idPress = self.canvas.mpl_connect('button_press_event', self.onMousePress)
		if not self._idRelease:
			self._idRelease = self.canvas.mpl_connect('button_release_event', self.onMouseRelease)
		if not self._idMotion:
			self._idMotion = self.canvas.mpl_connect('motion_notify_event', self.onMouseMove)

	def stopMouseCapture(self):
		if self._idPress:
			self.canvas.mpl_disconnect(self._idPress)
			self._idPress = None
		if self._idRelease:
			self.canvas.mpl_disconnect(self._idRelease)
			self._idRelease = None
		if self._idMotion:
			self.canvas.mpl_disconnect(self._idMotion)
			self._idMotion = None


	def onMousePress(self, event):
		if event.inaxes != self.canvas.axes: return

		self._startPoint = event.xdata, event.ydata

		self.vertices.append( self._startPoint )
		
		# left or middle button
		if event.button == 1 or event.button == 2:
			if len(self.vertices) == 1:
				if not self.currentClassName in self.drawnClasses:
					polygon = plt.Polygon(self.vertices, closed=True, alpha=0.2)
					self.drawnClasses[self.currentClassName] = {"polygon":polygon, "label":None}
					self.canvas.axes.add_patch( self.drawnClasses[self.currentClassName]["polygon"] )
				else:
# 					self.drawnClasses[self.currentClassName]["polygon"].remove()
# 					if self.drawnClasses[self.currentClassName]["label"]:
# 						self.drawnClasses[self.currentClassName]["label"].remove()
					rubberband = list(self.vertices)
					rubberband.append(self._startPoint)
					self.drawnClasses[self.currentClassName]["polygon"].set_xy(rubberband)
			
			if len(self.vertices) > 1:
				rubberband = list(self.vertices)
				rubberband.append(self._startPoint)
				self.drawnClasses[self.currentClassName]["polygon"].set_xy(rubberband)

		# if right button
		if event.button == 3:
			# remove last duplicated point setting last saved vertices
			self.drawnClasses[self.currentClassName]["polygon"].set_xy(self.vertices)
			
			# set label of the poligon in this last point
			label = self.canvas.axes.text(event.xdata, event.ydata, self.currentClassName)
			self.drawnClasses[self.currentClassName]["label"] = label
			
			# terminate editing
			self.stopMouseCapture()
			self._active = None
			self.mode = ''
			self.dlg.nav.set_message(self.mode)
			self.drawButton.setChecked(False)
					
		self.canvas.axes.draw_artist( self.drawnClasses[self.currentClassName]["polygon"] )
		self.canvas.draw()

	def onMouseRelease(self, event):
		#self._startPoint = None
		
		#self.stopMouseCapture()
		#self.resetActionsState()

		#self._active = None
		#self.mode = ''
		self.dlg.nav.set_message(self.mode)
		
		self.canvas.axes.draw_artist( self.drawnClasses[self.currentClassName]["polygon"] )
		self.canvas.draw()


	def onMouseMove(self, event):
		# override the cursor
		if event.inaxes and self._active in ['POLYGON']:
			self.dlg.nav.set_cursor( NavigationToolbar.Cursor.SELECT_REGION )

		#if not self._startPoint: return
		if event.inaxes != self.canvas.axes: return
		if len(self.vertices) == 0:	return

		currentPoint = event.xdata, event.ydata
		
		# create or update the line
		if self._active == 'POLYGON':
			rubberband = list(self.vertices)
			# add two times is a trick becaouse polygon print only n-1 vertices!
			rubberband.append(currentPoint)
			rubberband.append(currentPoint)
			
			self.drawnClasses[self.currentClassName]["polygon"].set_xy(rubberband)
			self.canvas.axes.draw_artist( self.drawnClasses[self.currentClassName]["polygon"] )
			
		# re-draw
		self.canvas.draw()
	
# 	def editPolygon(self):
# 		if not self.canvas.polygon:
# 			self.editPolygonAction.setChecked(False)
# 			return
# 
# 		if self.polyeditor:
# 			del self.polyeditor
# 			self.polyeditor = None
# 		
# 		if self.editPolygQIdentityProxyModel and columnonAction.isChecked():
# 			self.polyeditor = PathInteractor(self.canvas.polygon)


class PolygonSectionGraph(PlotWdg):

	def __init__(self, classificationMap, *args, **kwargs):
		PlotWdg.__init__(self,	*args, **kwargs)
		self.polygon = None
		self._classificationMap = classificationMap

	def _plot(self):
		# convert values, then create the plot
		x = map(Utils.valueFromQVariant, self.x)
		y = map(Utils.valueFromQVariant, self.y)

		# split values in 3 classes: shallow, deep and unclassified earthquakes
		classes = (shallow, deep, unclassified) = ( ([],[]), ([],[]), ([],[]) )
		for index in range(len(self.x)):
			fid = self.info[index]
			if not self._classificationMap.has_key( fid ):
				classData = classes[2]	# unclassified
			else:
				classData = classes[ self._classificationMap[ fid ] ]
			classData[0].append( self.x[index] )
			classData[1].append( self.y[index] )
		
		# plot the both the earthquakes classes
		if shallow[0] and shallow[1]:
			shallowItems = self.axes.scatter(shallow[0], shallow[1], marker='o', c='r')
			self.collections.append( shallowItems )

		if deep[0] and deep[1]:
			deepItems = self.axes.scatter(deep[0], deep[1], marker='o', c='b')
			self.collections.append( deepItems )

		if unclassified[0] and unclassified[1]:
			unclassifiedItems = self.axes.scatter(unclassified[0], unclassified[1], marker='x', c='k')
			self.collections.append( unclassifiedItems )


class NavigationToolbarPolygonSection(NavigationToolbar):
	def __init__(self, canvas, parent=None):
		NavigationToolbar.__init__(self, canvas, parent)

# 		self.polygonAction = QtGui.QAction( QtGui.QIcon(":/gem-mt_plugin/icons/polygon"), "Draw polygon", self )
# 		self.polygonAction.setToolTip( "Draw polygon" )
# 		self.polygonAction.setCheckable(True)
# 		self.insertAction(self.homeAction, self.polygonAction)
# 		self.connect(self.polygonAction, QtCore.SIGNAL("triggered()"), self.drawPolygon)
# 
# 		self.polyeditor = None
# 		self.editPolygonAction = QtGui.QAction( QtGui.QIcon(":/gem-mt_plugin/icons/editpolygon"), "Edit polygon", self )
# 		self.editPolygonAction.setToolTip( "Draw polygon" )
# 		self.editPolygonAction.setCheckable(True)
# 		self.insertAction(self.homeAction, self.editPolygonAction)
# 		self.connect(self.editPolygonAction, QtCore.SIGNAL("triggered()"), self.editPolygon)
# 		# avoid use editing for the moment
# 		self.editPolygonAction.setVisible(False)

		# add toolbutton to update the classification
		self.updateClassificationAction = QtGui.QAction( QtGui.QIcon(":/gem-mt_plugin/icons/refresh"), "Update classification", self )
		self.updateClassificationAction.setToolTip( "Update classification" )
		self.insertAction(self.homeAction, self.updateClassificationAction)
		self.connect(self.updateClassificationAction, QtCore.SIGNAL("triggered()"), self.updateClassification)

		self.insertSeparator(self.homeAction)

		# used in the mouse event handler
		self._startPoint = None
		self._idMotion = None


	def configure_subplots(self, *args):
		pass	# do nothing

	def updateClassification(self):
		self.emit( QtCore.SIGNAL("classificationUpdateRequested") )



class PathInteractor:
    """
    An path editor.

    Key-bindings

      't' toggle vertex markers on and off.  When vertex markers are on,
          you can move them, delete them
    """

    showverts = True
    epsilon = 5  # max pixel distance to count as a vertex hit

    def __init__(self, pathpatch):

        self.ax = pathpatch.axes
        canvas = self.ax.figure.canvas
        self.pathpatch = pathpatch
        self.pathpatch.set_animated(True)

        x, y = zip(*self.pathpatch.get_path().vertices)

        self.line, = self.ax.plot(x,y,marker='o', markerfacecolor='r', animated=True)
        self.line.set_visible(self.showverts)

        self._ind = None # the active vert

        canvas.mpl_connect('draw_event', self.draw_callback)
        canvas.mpl_connect('button_press_event', self.button_press_callback)
        #canvas.mpl_connect('key_press_event', self.key_press_callback)
        canvas.mpl_connect('button_release_event', self.button_release_callback)
        canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        self.canvas = canvas
        self.canvas.draw()

	def __del__(self):
		self.line.set_visible(False)

    def draw_callback(self, event):
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.ax.draw_artist(self.pathpatch)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)

    def pathpatch_changed(self, pathpatch):
        'this method is called whenever the pathpatchgon object is called'
        # only copy the artist props to the line (except visibility)
        vis = self.line.get_visible()
        plt.Artist.update_from(self.line, pathpatch)
        self.line.set_visible(vis)  # don't use the pathpatch visibility state


    def get_ind_under_point(self, event):
        'get the index of the vertex under point if within epsilon tolerance'

        # display coords
        xy = np.asarray(self.pathpatch.get_path().vertices)
        xyt = self.pathpatch.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.sqrt((xt-event.x)**2 + (yt-event.y)**2)
        ind = d.argmin()

        if d[ind]>=self.epsilon:
            ind = None

        return ind

    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        if not self.showverts: return
        if event.inaxes==None: return
        if event.button != 1: return
        self._ind = self.get_ind_under_point(event)

    def button_release_callback(self, event):
        'whenever a mouse button is released'
        if not self.showverts: return
        if event.button != 1: return
        self._ind = None

    def key_press_callback(self, event):
        'whenever a key is pressed'
        if not event.inaxes: return
        if event.key=='t':
            self.showverts = not self.showverts
            self.line.set_visible(self.showverts)
            if not self.showverts: self._ind = None

        self.canvas.draw()

    def motion_notify_callback(self, event):
        'on mouse movement'
        if not self.showverts: return
        if self._ind is None: return
        if event.inaxes is None: return
        if event.button != 1: return
        x,y = event.xdata, event.ydata

        vertices = self.pathpatch.get_path().vertices

        vertices[self._ind] = x,y
        self.line.set_data(zip(*vertices))

        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.pathpatch)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)


# class ClassificationTableModel(QtGui.QIdentityProxyModel):
# 	
# 	def __init__(self, parent=None):
# 		super(ClassificationTableModel, self).__init__(parent)
# 	
#   	def columnCount(self, index, parent):
#   		if not index.isValid():
#   			return
#   		row = index.row()
#   		if 
#   		return self.sourceModel().columnCount(index)+1 if self.sourceModel().column() > 0 else 0 
# 	
# 	def headerData(self, section, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
# 		if (section == self.sourceModel().index(section).column()+1) and role ==  QtCore.Qt.DisplayRole:
# 			return "Drawn"
# 		else:
# 			return self.sourceModel().headerData(section, orientation, role)
# 	
# 	def data(self, index, role=QtCore.Qt.DisplayRole):
# 		if not index.isValid():
# 			return
# 		
# 		if (index.column() == self.sourceModel().column()+1) and role ==  QtCore.Qt.DisplayRole:
# 			return "False"
# 		else:
# 			return self.sourceModel().data(index, role)
# 		
# 	def setDrawn(self, index=None, status=False):
# 		if not index or not status:
# 			return
# 		
# 		if not index.isValid():
# 			return
# 		
# 		value = "True" if status else "Flase"
# 		self.setData( index, value, QtCore.Qt.EditRole)


if __name__ == "__main__":
	# for command-line arguments
	import sys

	# Create the GUI application
	app = QtGui.QApplication(sys.argv)
	
	# show a cross-section plot
	PolygonSectionWdg( ([1,2,3,4,5],[10,9,7,4,0]), labels=("x", "y"), title="Cross section" ).show()

	# start the Qt main loop execution, exiting from this script
	# with the same return code of Qt application
	sys.exit(app.exec_())

