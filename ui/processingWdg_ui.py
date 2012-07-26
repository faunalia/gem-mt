# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/processingWdg.ui'
#
# Created: Wed Jul 25 05:48:12 2012
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
        self.algorithmCombo = QtGui.QComboBox(ProcessingWdg)
        self.algorithmCombo.setObjectName(_fromUtf8("algorithmCombo"))
        self.algorithmCombo.addItem(_fromUtf8(""))
        self.algorithmCombo.addItem(_fromUtf8(""))
        self.algorithmCombo.addItem(_fromUtf8(""))
        self.algorithmCombo.addItem(_fromUtf8(""))
        self.algorithmCombo.addItem(_fromUtf8(""))
        self.algorithmCombo.addItem(_fromUtf8(""))
        self.algorithmCombo.addItem(_fromUtf8(""))
        self.verticalLayout.addWidget(self.algorithmCombo)
        self.algorithmStacked = QtGui.QStackedWidget(ProcessingWdg)
        self.algorithmStacked.setObjectName(_fromUtf8("algorithmStacked"))
        self.gardnerWdg = GardnerKnopoffDeclusterWdg()
        self.gardnerWdg.setObjectName(_fromUtf8("gardnerWdg"))
        self.algorithmStacked.addWidget(self.gardnerWdg)
        self.afteranWdg = AfteranDeclusterWdg()
        self.afteranWdg.setObjectName(_fromUtf8("afteranWdg"))
        self.algorithmStacked.addWidget(self.afteranWdg)
        self.steppWdg = SteppCompletenessWdg()
        self.steppWdg.setObjectName(_fromUtf8("steppWdg"))
        self.algorithmStacked.addWidget(self.steppWdg)
        self.weichertWdg = WeichertRecurrenceWdg()
        self.weichertWdg.setObjectName(_fromUtf8("weichertWdg"))
        self.algorithmStacked.addWidget(self.weichertWdg)
        self.akiWdg = AkiRecurrenceWdg()
        self.akiWdg.setObjectName(_fromUtf8("akiWdg"))
        self.algorithmStacked.addWidget(self.akiWdg)
        self.kijkoWdg = KijkoMaximumMagnitudeWdg()
        self.kijkoWdg.setObjectName(_fromUtf8("kijkoWdg"))
        self.algorithmStacked.addWidget(self.kijkoWdg)
        self.makropoulosWdg = MakropoulosMaximumMagnitudeWdg()
        self.makropoulosWdg.setObjectName(_fromUtf8("makropoulosWdg"))
        self.algorithmStacked.addWidget(self.makropoulosWdg)
        self.verticalLayout.addWidget(self.algorithmStacked)

        self.retranslateUi(ProcessingWdg)
        self.algorithmStacked.setCurrentIndex(6)
        QtCore.QObject.connect(self.algorithmCombo, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), self.algorithmStacked.setCurrentIndex)
        QtCore.QMetaObject.connectSlotsByName(ProcessingWdg)

    def retranslateUi(self, ProcessingWdg):
        ProcessingWdg.setWindowTitle(QtGui.QApplication.translate("ProcessingWdg", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_5.setTitle(QtGui.QApplication.translate("ProcessingWdg", "Spatial filter", None, QtGui.QApplication.UnicodeUTF8))
        self.drawPolygonBtn.setText(QtGui.QApplication.translate("ProcessingWdg", "Draw", None, QtGui.QApplication.UnicodeUTF8))
        self.clearPolygonBtn.setText(QtGui.QApplication.translate("ProcessingWdg", "Clear", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ProcessingWdg", "Algorithm", None, QtGui.QApplication.UnicodeUTF8))
        self.algorithmCombo.setItemText(0, QtGui.QApplication.translate("ProcessingWdg", "Gardner and Knopoff", None, QtGui.QApplication.UnicodeUTF8))
        self.algorithmCombo.setItemText(1, QtGui.QApplication.translate("ProcessingWdg", "Afteran", None, QtGui.QApplication.UnicodeUTF8))
        self.algorithmCombo.setItemText(2, QtGui.QApplication.translate("ProcessingWdg", "Stepp", None, QtGui.QApplication.UnicodeUTF8))
        self.algorithmCombo.setItemText(3, QtGui.QApplication.translate("ProcessingWdg", "Weichert", None, QtGui.QApplication.UnicodeUTF8))
        self.algorithmCombo.setItemText(4, QtGui.QApplication.translate("ProcessingWdg", "Aki", None, QtGui.QApplication.UnicodeUTF8))
        self.algorithmCombo.setItemText(5, QtGui.QApplication.translate("ProcessingWdg", "Kijko", None, QtGui.QApplication.UnicodeUTF8))
        self.algorithmCombo.setItemText(6, QtGui.QApplication.translate("ProcessingWdg", "Makropoulos & Burton", None, QtGui.QApplication.UnicodeUTF8))

from ..completeness_wdg import SteppCompletenessWdg
from ..recurrence_wdg import AkiRecurrenceWdg, WeichertRecurrenceWdg
from ..decluster_wdg import GardnerKnopoffDeclusterWdg, AfteranDeclusterWdg
from ..maximum_magnitude_wdg import KijkoMaximumMagnitudeWdg, MakropoulosMaximumMagnitudeWdg
