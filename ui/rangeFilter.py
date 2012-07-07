# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : RangeFilter
Description          : Int/Double/Date filter for ranges
Date                 : Jun 20, 2012 
copyright            : (C) 2012 by Giuseppe Sucameli
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

from PyQt4 import QtGui, QtCore
from rangeSlider import RangeSlider

class RangeFilter(QtGui.QWidget):
    def __init__(self, *args):
        super(RangeFilter, self).__init__(*args)

        self._createSpinBoxes()
        self._createSlider()

        self.setMinimum(0)
        self.setMaximum(100)
        self.setLowValue(0)
        self.setHighValue(100)

        self.recreateUi()

    def _createSpinBoxes(self):
        self.minSpin = QtGui.QSpinBox(self)
        self.maxSpin = QtGui.QSpinBox(self)
        self.connect( self.minSpin, QtCore.SIGNAL("valueChanged(int)"), self.setLowValue )
        self.connect( self.maxSpin, QtCore.SIGNAL("valueChanged(int)"), self.setHighValue )

    def _createSlider(self):
        self.slider = RangeSlider(self)
        self.connect( self.slider, QtCore.SIGNAL("lowValueChanged"), self._sliderLowValueChanged )
        self.connect( self.slider, QtCore.SIGNAL("highValueChanged"), self._sliderHighValueChanged )

    def recreateUi(self):
        layout = self.layout()
        if not layout:
            layout = QtGui.QGridLayout(self)
            layout.setMargin(0)
            self.setLayout( layout )

        else:
            layout.removeWidget(self.maxSpin)
            layout.removeWidget(self.slider)
            layout.removeWidget(self.minSpin)

        if self.slider.orientation() == QtCore.Qt.Horizontal:
            layout.addWidget(self.minSpin, 0, 0)
            layout.addWidget(self.slider, 0, 1)
            layout.addWidget(self.maxSpin, 0, 2)
            self.slider.setMinimumSize(QtCore.QSize(30, 0))

        else:
            layout.addWidget(self.maxSpin, 0, 0)
            layout.addWidget(self.slider, 1, 0)
            layout.addWidget(self.minSpin, 2, 0)
            self.slider.setMinimumSize(QtCore.QSize(0, 30))


    def orientation(self):
        return self.slider.orientation()

    def setOrientation(self, val):
        self.slider.setOrientation( val )
        self.recreateUi()

    def isActive(self):
        if self.lowValue() > self.minimum(): return True
        if self.highValue() < self.maximum(): return True
        return False


    def checkValue(self, val):
        val = self._getValue(val)
        return val is not None and val >= self.lowValue() and val <= self.highValue()


    def _toSliderValue(self, val):
        return val

    def _fromSliderValue(self, val):
        return val


    def minimum(self):
        return self.minSpin.minimum()

    def maximum(self):
        return self.maxSpin.maximum()

    def setMinimum(self, val):
        self.minSpin.setMinimum(val)
        self.maxSpin.setMinimum(val)
        self.slider.setMinimum( self._toSliderValue(val) )

    def setMaximum(self, val):
        self.minSpin.setMaximum(val)
        self.maxSpin.setMaximum(val)
        self.slider.setMaximum( self._toSliderValue(val) )

        # avoid resizing when the max value changes
        self.minSpin.setFixedSize( self.minSpin.sizeHint() )


    def lowValue(self):
        return self.minSpin.value()

    def highValue(self):
        return self.maxSpin.value()

    def setLowValue(self, val):
        self.minSpin.blockSignals(True)
        self.slider.blockSignals(True)
        self.minSpin.setValue( val )
        self.maxSpin.setMinimum( val )
        self.slider.setLowValue( self._toSliderValue(val) )
        self.minSpin.blockSignals(False)
        self.slider.blockSignals(False)
        self.emit( QtCore.SIGNAL("lowValueChanged"), val )

    def setHighValue(self, val):
        self.maxSpin.blockSignals(True)
        self.slider.blockSignals(True)
        self.maxSpin.setValue( val )
        self.minSpin.setMaximum( val )
        self.slider.setHighValue( self._toSliderValue(val) )
        self.maxSpin.blockSignals(False)
        self.slider.blockSignals(False)
        self.emit( QtCore.SIGNAL("highValueChanged"), val )

    def _sliderLowValueChanged(self, val):
        self.setLowValue( self._fromSliderValue(val) )

    def _sliderHighValueChanged(self, val):
        self.setHighValue( self._fromSliderValue(val) )


    @classmethod
    def _getValue(self, val):
        if isinstance(val, QtCore.QVariant): 
            intval, ok = val.toInt()
            if val.isValid() and ok:
                return intval
            return
        return val


class DoubleRangeFilter(RangeFilter):
    def __init__(self, *args):
        super(DoubleRangeFilter, self).__init__(*args)

    def _createSpinBoxes(self):
        self.minSpin = QtGui.QDoubleSpinBox(self)
        self.maxSpin = QtGui.QDoubleSpinBox(self)

        self.connect( self.minSpin, QtCore.SIGNAL("valueChanged(double)"), self.setLowValue )
        self.connect( self.maxSpin, QtCore.SIGNAL("valueChanged(double)"), self.setHighValue )


    def decimals(self):
        return self.minSpin.decimals()

    def setDecimals(self, val):
        self.minSpin.setDecimals(val)
        self.maxSpin.setDecimals(val)
        self.slider.setMinimum( self._toSliderValue(self.minimum()) )
        self.slider.setMaximum( self._toSliderValue(self.maximum()) )


    def _toSliderValue(self, val):
        return val * (10**self.decimals())

    def _fromSliderValue(self, val):
        return float(val) / (10**self.decimals())


    @classmethod
    def _getValue(self, val):
        if isinstance(val, QtCore.QVariant): 
            realval, ok = val.toDouble()
            if val.isValid() and ok:
                return realval
            return
        return val


class DateRangeFilter(RangeFilter):
    def __init__(self, *args):
        super(DateRangeFilter, self).__init__(*args)

    def _createSpinBoxes(self):
        self.minSpin = QtGui.QDateEdit(self)
        self.maxSpin = QtGui.QDateEdit(self)

        self.minSpin.setCalendarPopup(True)
        self.minSpin.setDisplayFormat("yyyy.MM.dd")#QtCore.QLocale.system().dateFormat(QtCore.QLocale.ShortFormat))
        self.maxSpin.setCalendarPopup(True)
        self.maxSpin.setDisplayFormat("yyyy.MM.dd")#QtCore.QLocale.system().dateFormat(QtCore.QLocale.ShortFormat))

        minFunc = lambda obj: self._fixupDateTime(obj.minimumDateTime()).toTime_t()
        maxFunc = lambda obj: self._fixupDateTime(obj.maximumDateTime()).toTime_t()
        valueFunc = lambda obj: self._fixupDateTime(obj.dateTime()).toTime_t()
        setMinFunc = lambda obj, val: obj.setMinimumDateTime( self._convertToDateTime( val ) )
        setMaxFunc = lambda obj, val: obj.setMaximumDateTime( self._convertToDateTime( val ) )
        setValueFunc = lambda obj, val: obj.setDateTime( self._convertToDateTime( val ) )

        self.minSpin.minimum = lambda: minFunc( self.minSpin )
        self.minSpin.maximum = lambda: maxFunc( self.minSpin )
        self.minSpin.value = lambda: valueFunc( self.minSpin )
        self.minSpin.setMinimum = lambda val: setMinFunc( self.minSpin, val )
        self.minSpin.setMaximum = lambda val: setMaxFunc( self.minSpin, val )
        self.minSpin.setValue = lambda val: setValueFunc( self.minSpin, val )

        self.maxSpin.minimum = lambda: minFunc( self.maxSpin )
        self.maxSpin.maximum = lambda: maxFunc( self.maxSpin )
        self.maxSpin.value = lambda: valueFunc( self.maxSpin )
        self.maxSpin.setMinimum = lambda val: setMinFunc( self.maxSpin, val )
        self.maxSpin.setMaximum = lambda val: setMaxFunc( self.maxSpin, val )
        self.maxSpin.setValue = lambda val: setValueFunc( self.maxSpin, val )

        self.connect( self.minSpin, QtCore.SIGNAL("dateChanged(const QDate &)"), self.setLowValue )
        self.connect( self.maxSpin, QtCore.SIGNAL("dateChanged(const QDate &)"), self.setHighValue )

    def minimumDate(self):
        return self.minSpin.minimumDate()

    def maximumDate(self):
        return self.maxSpin.maximumDate()

    def lowValueDate(self):
        return self.minSpin.date()

    def highValueDate(self):
        return self.maxSpin.date()

    def _sliderLowValueChanged(self, val):
        #print val, self._fromSliderValue(val), self.slider.minimum(), self.slider.maximum()
        self.setLowValue( self._fromSliderValue(val) )

    def _sliderHighValueChanged(self, val):
        #print val, self._fromSliderValue(val), self.slider.minimum(), self.slider.maximum()
        self.setHighValue( self._fromSliderValue(val) )


    def _toSliderValue(self, val):
        return (self._convertToValue( val ) - self.minimum())/3600

    def _fromSliderValue(self, val):
        return self._convertToValue( val*3600 + self.minimum() )


    @classmethod
    def _getValue(self, val):
        if not isinstance(val, QtCore.QVariant): 
            return self._convertToValue( val )

        if not val.isValid(): return

        ok = False
        if val.type() == QtCore.QVariant.Int:
            newval, ok = val.toInt()
        elif val.type() in (QtCore.QVariant.Date, QtCore.QVariant.DateTime, QtCore.QVariant.String):
            newval = val.toDateTime()
            ok = newval.isValid()

        if not ok: return

        return self._convertToValue( newval )

    @classmethod
    def _convertToDateTime(self, val):
        if isinstance(val, (int,long)):
            return self._fixupDateTime( QtCore.QDateTime.fromTime_t(val) )
        elif isinstance(val, QtCore.QDate):
            return QtCore.QDateTime(val, QtCore.QTime(0,0,0))
        elif isinstance(val, QtCore.QDateTime):
             return self._fixupDateTime( val )

    @classmethod
    def _convertToValue(self, val):
        dt = self._convertToDateTime(val)
        if dt:
            return self._fixupDateTime( dt ).toTime_t()

    @classmethod
    def _fixupDateTime(self, dt):
        dt.setTime(QtCore.QTime(0,0,0))
        return dt


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)

    rangeFilter = RangeFilter()
    rangeFilter.setMinimum(0)
    rangeFilter.setMaximum(10000)
    rangeFilter.setLowValue(0)
    rangeFilter.setHighValue(10000)
    rangeFilter.setOrientation( QtCore.Qt.Horizontal )

    def echo(value):
        print value
    QtCore.QObject.connect(rangeFilter, QtCore.SIGNAL('lowValueChanged'), echo)
    QtCore.QObject.connect(rangeFilter, QtCore.SIGNAL('highValueChanged'), echo)

    rangeFilter.show()
    sys.exit(app.exec_())

