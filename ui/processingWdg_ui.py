# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/processingWdg.ui'
#
# Created: Sat Sep 15 04:26:03 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ProcessingWdg(object):
    def setupUi(self, ProcessingWdg):
        ProcessingWdg.setObjectName(_fromUtf8("ProcessingWdg"))
        ProcessingWdg.resize(279, 289)
        self.verticalLayout = QtGui.QVBoxLayout(ProcessingWdg)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox_5 = QtGui.QGroupBox(ProcessingWdg)
        self.groupBox_5.setObjectName(_fromUtf8("groupBox_5"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox_5)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.drawPolygonBtn = QtGui.QToolButton(self.groupBox_5)
        self.drawPolygonBtn.setCheckable(True)
        self.drawPolygonBtn.setObjectName(_fromUtf8("drawPolygonBtn"))
        self.horizontalLayout.addWidget(self.drawPolygonBtn)
        self.clearPolygonBtn = QtGui.QToolButton(self.groupBox_5)
        self.clearPolygonBtn.setObjectName(_fromUtf8("clearPolygonBtn"))
        self.horizontalLayout.addWidget(self.clearPolygonBtn)
        self.verticalLayout.addWidget(self.groupBox_5)
        self.label = QtGui.QLabel(ProcessingWdg)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.moduleCombo = QtGui.QComboBox(ProcessingWdg)
        self.moduleCombo.setObjectName(_fromUtf8("moduleCombo"))
        self.moduleCombo.addItem(_fromUtf8(""))
        self.moduleCombo.addItem(_fromUtf8(""))
        self.moduleCombo.addItem(_fromUtf8(""))
        self.moduleCombo.addItem(_fromUtf8(""))
        self.verticalLayout.addWidget(self.moduleCombo)
        self.algorithmStacked = QtGui.QStackedWidget(ProcessingWdg)
        self.algorithmStacked.setObjectName(_fromUtf8("algorithmStacked"))
        self.declusterWdg = DeclusterWdg()
        self.declusterWdg.setObjectName(_fromUtf8("declusterWdg"))
        self.algorithmStacked.addWidget(self.declusterWdg)
        self.completenessWdg = CompletenessWdg()
        self.completenessWdg.setObjectName(_fromUtf8("completenessWdg"))
        self.algorithmStacked.addWidget(self.completenessWdg)
        self.recurrenceWdg = RecurrenceWdg()
        self.recurrenceWdg.setObjectName(_fromUtf8("recurrenceWdg"))
        self.algorithmStacked.addWidget(self.recurrenceWdg)
        self.maxMagnitudeWdg = MaximumMagnitudeWdg()
        self.maxMagnitudeWdg.setObjectName(_fromUtf8("maxMagnitudeWdg"))
        self.algorithmStacked.addWidget(self.maxMagnitudeWdg)
        self.verticalLayout.addWidget(self.algorithmStacked)

        self.retranslateUi(ProcessingWdg)
        self.algorithmStacked.setCurrentIndex(2)
        QtCore.QObject.connect(self.moduleCombo, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), self.algorithmStacked.setCurrentIndex)
        QtCore.QMetaObject.connectSlotsByName(ProcessingWdg)

    def retranslateUi(self, ProcessingWdg):
        ProcessingWdg.setWindowTitle(QtGui.QApplication.translate("ProcessingWdg", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_5.setTitle(QtGui.QApplication.translate("ProcessingWdg", "Spatial filter", None, QtGui.QApplication.UnicodeUTF8))
        self.drawPolygonBtn.setText(QtGui.QApplication.translate("ProcessingWdg", "Draw", None, QtGui.QApplication.UnicodeUTF8))
        self.clearPolygonBtn.setText(QtGui.QApplication.translate("ProcessingWdg", "Clear", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ProcessingWdg", "Method", None, QtGui.QApplication.UnicodeUTF8))
        self.moduleCombo.setItemText(0, QtGui.QApplication.translate("ProcessingWdg", "Decluster", None, QtGui.QApplication.UnicodeUTF8))
        self.moduleCombo.setItemText(1, QtGui.QApplication.translate("ProcessingWdg", "Completeness", None, QtGui.QApplication.UnicodeUTF8))
        self.moduleCombo.setItemText(2, QtGui.QApplication.translate("ProcessingWdg", "Recurrence", None, QtGui.QApplication.UnicodeUTF8))
        self.moduleCombo.setItemText(3, QtGui.QApplication.translate("ProcessingWdg", "Maximum magnitude", None, QtGui.QApplication.UnicodeUTF8))

from ..decluster_wdg import DeclusterWdg
from ..recurrence_wdg import RecurrenceWdg
from ..completeness_wdg import CompletenessWdg
from ..maximum_magnitude_wdg import MaximumMagnitudeWdg
