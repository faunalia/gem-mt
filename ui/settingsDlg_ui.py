# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/settingsDlg.ui'
#
# Created: Wed Jul 18 12:18:54 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(400, 315)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.groupBox = QtGui.QGroupBox(Dialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout_2.addWidget(self.label, 2, 0, 1, 1)
        self.magnitudeEdit = QtGui.QLineEdit(self.groupBox)
        self.magnitudeEdit.setText(_fromUtf8("MAG"))
        self.magnitudeEdit.setObjectName(_fromUtf8("magnitudeEdit"))
        self.gridLayout_2.addWidget(self.magnitudeEdit, 2, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout_2.addWidget(self.label_2, 3, 0, 1, 1)
        self.depthEdit = QtGui.QLineEdit(self.groupBox)
        self.depthEdit.setText(_fromUtf8("DEPTH"))
        self.depthEdit.setObjectName(_fromUtf8("depthEdit"))
        self.gridLayout_2.addWidget(self.depthEdit, 3, 1, 1, 1)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout_2.addWidget(self.label_3, 4, 0, 1, 1)
        self.dateEdit = QtGui.QLineEdit(self.groupBox)
        self.dateEdit.setText(_fromUtf8("DATE"))
        self.dateEdit.setObjectName(_fromUtf8("dateEdit"))
        self.gridLayout_2.addWidget(self.dateEdit, 4, 1, 1, 1)
        self.gridLayout.addWidget(self.groupBox, 1, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 2)
        self.groupBox_2 = QtGui.QGroupBox(Dialog)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.gridLayout_3 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.label_4 = QtGui.QLabel(self.groupBox_2)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout_3.addWidget(self.label_4, 0, 0, 1, 1)
        self.delimiterCombo = QtGui.QComboBox(self.groupBox_2)
        self.delimiterCombo.setEditable(True)
        self.delimiterCombo.setObjectName(_fromUtf8("delimiterCombo"))
        self.delimiterCombo.addItem(_fromUtf8(""))
        self.delimiterCombo.setItemText(0, _fromUtf8(","))
        self.delimiterCombo.addItem(_fromUtf8(""))
        self.delimiterCombo.setItemText(1, _fromUtf8(",(?!\\s)"))
        self.gridLayout_3.addWidget(self.delimiterCombo, 0, 1, 1, 1)
        self.label_6 = QtGui.QLabel(self.groupBox_2)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout_3.addWidget(self.label_6, 1, 0, 1, 1)
        self.longEdit = QtGui.QLineEdit(self.groupBox_2)
        self.longEdit.setText(_fromUtf8("LONG"))
        self.longEdit.setObjectName(_fromUtf8("longEdit"))
        self.gridLayout_3.addWidget(self.longEdit, 1, 1, 1, 1)
        self.label_5 = QtGui.QLabel(self.groupBox_2)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout_3.addWidget(self.label_5, 2, 0, 1, 1)
        self.latEdit = QtGui.QLineEdit(self.groupBox_2)
        self.latEdit.setText(_fromUtf8("LAT"))
        self.latEdit.setObjectName(_fromUtf8("latEdit"))
        self.gridLayout_3.addWidget(self.latEdit, 2, 1, 1, 1)
        self.gridLayout.addWidget(self.groupBox_2, 0, 0, 1, 2)

        self.retranslateUi(Dialog)
        self.delimiterCombo.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.magnitudeEdit, self.depthEdit)
        Dialog.setTabOrder(self.depthEdit, self.dateEdit)
        Dialog.setTabOrder(self.dateEdit, self.buttonBox)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Filter settings", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Magnitude", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "Depth", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "Date", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("Dialog", "CSV settings", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Dialog", "Delimiter (reg. expr.)", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("Dialog", "Latitude", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("Dialog", "Longitude", None, QtGui.QApplication.UnicodeUTF8))

