# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/classificationWdg.ui'
#
# Created: Fri Jul  6 18:26:30 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ClassificationWdg(object):
    def setupUi(self, ClassificationWdg):
        ClassificationWdg.setObjectName(_fromUtf8("ClassificationWdg"))
        ClassificationWdg.resize(275, 334)
        self.verticalLayout = QtGui.QVBoxLayout(ClassificationWdg)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox_2 = QtGui.QGroupBox(ClassificationWdg)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.drawAreaBtn = QtGui.QToolButton(self.groupBox_2)
        self.drawAreaBtn.setCheckable(True)
        self.drawAreaBtn.setObjectName(_fromUtf8("drawAreaBtn"))
        self.gridLayout_2.addWidget(self.drawAreaBtn, 0, 0, 1, 1)
        self.clearAreaBtn = QtGui.QToolButton(self.groupBox_2)
        self.clearAreaBtn.setObjectName(_fromUtf8("clearAreaBtn"))
        self.gridLayout_2.addWidget(self.clearAreaBtn, 0, 1, 1, 1)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.groupBox = QtGui.QGroupBox(ClassificationWdg)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.addBufferBtn = QtGui.QToolButton(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addBufferBtn.sizePolicy().hasHeightForWidth())
        self.addBufferBtn.setSizePolicy(sizePolicy)
        self.addBufferBtn.setCheckable(True)
        self.addBufferBtn.setObjectName(_fromUtf8("addBufferBtn"))
        self.gridLayout.addWidget(self.addBufferBtn, 0, 2, 1, 1)
        self.delBufferBtn = QtGui.QToolButton(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.delBufferBtn.sizePolicy().hasHeightForWidth())
        self.delBufferBtn.setSizePolicy(sizePolicy)
        self.delBufferBtn.setObjectName(_fromUtf8("delBufferBtn"))
        self.gridLayout.addWidget(self.delBufferBtn, 1, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(37, 50, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 2, 1, 1)
        self.buffersTable = QtGui.QTableView(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buffersTable.sizePolicy().hasHeightForWidth())
        self.buffersTable.setSizePolicy(sizePolicy)
        self.buffersTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.buffersTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.buffersTable.setObjectName(_fromUtf8("buffersTable"))
        self.buffersTable.horizontalHeader().setStretchLastSection(True)
        self.gridLayout.addWidget(self.buffersTable, 0, 0, 5, 2)
        self.crossSectionBtn = QtGui.QPushButton(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.crossSectionBtn.sizePolicy().hasHeightForWidth())
        self.crossSectionBtn.setSizePolicy(sizePolicy)
        self.crossSectionBtn.setObjectName(_fromUtf8("crossSectionBtn"))
        self.gridLayout.addWidget(self.crossSectionBtn, 3, 2, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Maximum)
        self.gridLayout.addItem(spacerItem1, 2, 2, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.displayClassifiedDataBtn = QtGui.QPushButton(ClassificationWdg)
        self.displayClassifiedDataBtn.setObjectName(_fromUtf8("displayClassifiedDataBtn"))
        self.verticalLayout.addWidget(self.displayClassifiedDataBtn)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)

        self.retranslateUi(ClassificationWdg)
        QtCore.QMetaObject.connectSlotsByName(ClassificationWdg)

    def retranslateUi(self, ClassificationWdg):
        ClassificationWdg.setWindowTitle(QtGui.QApplication.translate("ClassificationWdg", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("ClassificationWdg", "Define area of interest", None, QtGui.QApplication.UnicodeUTF8))
        self.drawAreaBtn.setText(QtGui.QApplication.translate("ClassificationWdg", "Draw", None, QtGui.QApplication.UnicodeUTF8))
        self.clearAreaBtn.setText(QtGui.QApplication.translate("ClassificationWdg", "Clear", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("ClassificationWdg", "Classification buffers", None, QtGui.QApplication.UnicodeUTF8))
        self.addBufferBtn.setText(QtGui.QApplication.translate("ClassificationWdg", "New", None, QtGui.QApplication.UnicodeUTF8))
        self.delBufferBtn.setText(QtGui.QApplication.translate("ClassificationWdg", "Delete", None, QtGui.QApplication.UnicodeUTF8))
        self.crossSectionBtn.setText(QtGui.QApplication.translate("ClassificationWdg", "Open the \n"
"cross section", None, QtGui.QApplication.UnicodeUTF8))
        self.displayClassifiedDataBtn.setText(QtGui.QApplication.translate("ClassificationWdg", "Display classified earthquakes", None, QtGui.QApplication.UnicodeUTF8))

