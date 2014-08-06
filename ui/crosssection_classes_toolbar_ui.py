# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/crosssection_classes_toolbar.ui'
#
# Created: Wed Aug  6 15:08:50 2014
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_crossSectionClassesToolbar(object):
    def setupUi(self, crossSectionClassesToolbar):
        crossSectionClassesToolbar.setObjectName(_fromUtf8("crossSectionClassesToolbar"))
        crossSectionClassesToolbar.resize(151, 314)
        self.verticalLayout_2 = QtGui.QVBoxLayout(crossSectionClassesToolbar)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setMargin(0)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.classesTable = QtGui.QTableView(crossSectionClassesToolbar)
        self.classesTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.classesTable.setObjectName(_fromUtf8("classesTable"))
        self.verticalLayout_2.addWidget(self.classesTable)
        self.drawButton = QtGui.QPushButton(crossSectionClassesToolbar)
        self.drawButton.setCheckable(True)
        self.drawButton.setObjectName(_fromUtf8("drawButton"))
        self.verticalLayout_2.addWidget(self.drawButton)
        self.removeButton = QtGui.QPushButton(crossSectionClassesToolbar)
        self.removeButton.setObjectName(_fromUtf8("removeButton"))
        self.verticalLayout_2.addWidget(self.removeButton)

        self.retranslateUi(crossSectionClassesToolbar)
        QtCore.QMetaObject.connectSlotsByName(crossSectionClassesToolbar)

    def retranslateUi(self, crossSectionClassesToolbar):
        self.drawButton.setText(QtGui.QApplication.translate("crossSectionClassesToolbar", "Draw", None, QtGui.QApplication.UnicodeUTF8))
        self.removeButton.setText(QtGui.QApplication.translate("crossSectionClassesToolbar", "Remove", None, QtGui.QApplication.UnicodeUTF8))

