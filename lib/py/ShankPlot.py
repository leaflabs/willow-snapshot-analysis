#!/usr/bin/python

from PyQt4 import QtCore, QtGui

import os, sys, time, h5py
sys.setrecursionlimit(10000) # this is necessary to mutually link >140 plot axes

import pyqtgraph as pg
pg.setConfigOptions(antialias=True)

import numpy as np

import pickle, glob

from SpikeScopeWindow import SpikeScopeWindow
from WillowDataset import WillowDataset

################

def subplotIndex2rowColChan(subplotIndex, probeMap, shank):
    # here's some mangling that's necessary b.c. pyqtgraph plots subplots in
    #   column-major order
    ncols = probeMap['ncols']
    row = subplotIndex // ncols
    col = subplotIndex % ncols
    willowChan = probeMap[shank, row, col]
    return row, col, willowChan

####
# main widget classes

class HelpWindow(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)

        usageText = ("<center><b>Usage:</b></center>"
                    "<ul>"
                    "<li>Mousewheel scrolls through probe-mapped channels</li>"
                    "<li>Ctrl-Plus and Ctrl-Minus expands or contracts the plot canvas vertically</li>"
                    "<li>Ctrl-Mousewheel over a plot zooms horizontally</li>"
                    "<li>Ctrl-Shift-Mousewheel over a plot zooms vertically</li>"
                    "<li>By default, all plot axes are locked together. To unlock them, uncheck the 'Lock Plots Together' box in the control panel</li>"
                    "<li>Double-click on a plot to open a SpikeScope window for that channel</li>"
                    "<li>Channel numbers are 0-indexed, and in reference to the 1024-channel Willow dataspace</li>"
                    "<li>y-axes have units of microVolts (uV), x-axes have units of milliseconds (ms)</li>"
                    "</ul>")
        self.usageLabel = QtGui.QLabel(usageText)
        self.usageLabel.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.usageLabel)
        self.setLayout(layout)

        self.setWindowTitle('Help')
        self.setWindowIcon(QtGui.QIcon('../lib/img/leaflabs_logo.png'))


class ControlPanel(QtGui.QWidget):

    filterToggled = QtCore.pyqtSignal(bool)
    axesToggled = QtCore.pyqtSignal(bool)
    lockToggled = QtCore.pyqtSignal(bool) 
    defaultSelected = QtCore.pyqtSignal(bool) 
    impedanceFileSelected = QtCore.pyqtSignal(str) 

    def __init__(self, dataset, impedanceFile):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset
        self.impedanceFile = impedanceFile

        self.filterCheckbox = QtGui.QCheckBox('Display Filtered')
        self.filterCheckbox.setChecked(True)
        self.filterCheckbox.stateChanged.connect(self.toggleFiltered)

        self.axesCheckbox = QtGui.QCheckBox('Display Axes')
        self.axesCheckbox.setChecked(True)
        self.axesCheckbox.stateChanged.connect(self.toggleAxes)

        self.lockCheckbox = QtGui.QCheckBox('Lock Plots Together')
        self.lockCheckbox.setChecked(True)
        self.lockCheckbox.stateChanged.connect(self.toggleLock)

        if self.impedanceFile:
            self.impedanceFileButton = QtGui.QPushButton(
                                    os.path.basename(self.impedanceFile))
        else:
            self.impedanceFileButton = QtGui.QPushButton('(impedance file)')
        self.impedanceFileButton.setToolTip('Set Impedance File')
        self.impedanceFileButton.clicked.connect(self.selectImpedanceFile)

        self.defaultButton = QtGui.QPushButton()
        self.defaultButton.setIcon(QtGui.QIcon('../lib/img/home.png'))
        self.defaultButton.setToolTip('Restore Defaults')
        self.defaultButton.clicked.connect(self.restoreDefault)
        self.defaultButton.setMaximumWidth(80)
        self.defaultButton.setMaximumHeight(80)

        self.helpButton = QtGui.QPushButton()
        self.helpButton.setIcon(QtGui.QIcon('../lib/img/help.png'))
        self.helpButton.setToolTip('Help')
        self.helpButton.setMaximumWidth(80)
        self.helpButton.setMaximumHeight(80)
        self.helpWindow = HelpWindow()
        self.helpButton.clicked.connect(self.launchHelpWindow)

        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.filterCheckbox)
        #self.layout.addWidget(self.spikeDetectCheckbox)
        self.layout.addWidget(self.axesCheckbox)
        self.layout.addWidget(self.lockCheckbox)
        self.layout.addWidget(self.impedanceFileButton)
        self.layout.addWidget(self.defaultButton)
        self.layout.addWidget(self.helpButton)
        self.setLayout(self.layout)

    def selectImpedanceFile(self):
        if self.impedanceFile:
            d = os.path.dirname(self.impedanceFile)
        else:
            d = os.path.dirname(self.dataset.filename)
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Select Impedance File', d)
        if filename:
            self.impedanceFile = str(filename)
            self.impedanceFileButton.setText(os.path.basename(self.impedanceFile))
            self.impedanceFileSelected.emit(self.impedanceFile)

    def restoreDefault(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.filterCheckbox.setChecked(True)
        self.axesCheckbox.setChecked(True)
        self.lockCheckbox.setChecked(True)
        self.defaultSelected.emit(self.filterCheckbox.isChecked())
        QtGui.QApplication.restoreOverrideCursor()

    def launchHelpWindow(self):
        self.helpWindow.show()

    def toggleFiltered(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.filterToggled.emit(self.filterCheckbox.isChecked())
        QtGui.QApplication.restoreOverrideCursor()

    def toggleAxes(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.axesToggled.emit(self.axesCheckbox.isChecked())
        QtGui.QApplication.restoreOverrideCursor()

    def toggleLock(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.lockToggled.emit(self.lockCheckbox.isChecked())
        QtGui.QApplication.restoreOverrideCursor()


class ScrollZoomPanel(QtGui.QScrollArea):
    """
    Basically a ScrollArea which automatically expands its widget to fill
    the area horizontally. The vertical extent is adjustable via the
    verticalZoom() method, which can be linked to Ctrl+Plus/Minus,
    Ctrl+Mousewheel, etc.
    """

    def __init__(self, widget):
        QtGui.QScrollArea.__init__(self)

        self.setWidget(widget)
        self.setAlignment(QtCore.Qt.AlignCenter)

    def resizeEvent(self, event):
        """
        Expands the widget to fill the QScrollArea
        """
        widget = self.widget()
        widget.resize(event.size().width(), widget.size().height())
        #widget.resize(event.size().width(), event.size().height())
        QtGui.QScrollArea.resizeEvent(self, event)
        event.accept()

    def verticalZoom(self, delta):
        """
        Expands the widget vertically
        """
        w = self.widget()
        curSize = w.size()
        x,y = curSize.width(), curSize.height()
        if delta > 0:
            y *= 1.5
        elif delta < 0:
            y /= 1.5
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        w.resize(x, y)
        QtGui.QApplication.restoreOverrideCursor()

class ClickablePlotItem(pg.PlotItem):

    def __init__(self, dataset, chan, row, col, *args, **kwargs):
        pg.PlotItem.__init__(self, *args, **kwargs)

        self.dataset = dataset
        self.chan = chan
        self.slice_idx = self.dataset.chan2slice_idx[chan]
        self.row = row
        self.col = col
        self.getAxis('left').setStyle(textFillLimits=[(3,0.05)], tickLength=5)
        self.getAxis('bottom').setStyle(tickLength=5)
        self.setTitle(title='Row %d, Col %d, Chan %d' % (self.row, self.col, self.chan))

        # install event filter for viewbox and axes items
        self.vb.installEventFilter(self)
        for axesDict in self.axes.values():
            axesDict['item'].installEventFilter(self)

    def mouseDoubleClickEvent(self, event):
        self.spikeScopeWindow = SpikeScopeWindow(self.dataset, self.chan)
        self.spikeScopeWindow.show()

    def plotRaw(self, dim=False):
        self.clear()
        pen = 0.2 if dim else (143,219,144)
        self.plot(x=self.dataset.time_ms,
                  y=self.dataset.slice_uv[self.slice_idx,:], pen=pen)
        self.setYRange(self.dataset.slice_min,
                       self.dataset.slice_max, padding=0.9)

    def plotFiltered(self, dim=False):
        self.clear()
        pen = 0.2 if dim else (143,219,144)
        self.plot(x=self.dataset.time_ms,
                  y=self.dataset.slice_filtered[self.slice_idx], pen=pen)
        self.setYRange(self.dataset.slice_filtered_min,
                       self.dataset.slice_filtered_max, padding=0.9)

    def eventFilter(self, target, ev):
        if ev.type() == QtCore.QEvent.GraphicsSceneWheel:
            if ev.modifiers() == QtCore.Qt.ControlModifier:
                self.axes['bottom']['item'].wheelEvent(ev)
            elif ev.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                self.axes['left']['item'].wheelEvent(ev)
            return True
        return False

class MultiPlotWidget(pg.GraphicsLayoutWidget):

    def __init__(self, dataset, probeMap, shank, impedanceFile):
        pg.GraphicsLayoutWidget.__init__(self)
        self.dataset = dataset
        self.probeMap = probeMap
        self.shank = shank

        self.ncols = self.probeMap['ncols']
        self.nrows = self.probeMap['nrows']
        self.nchannels = self.ncols * self.nrows

        self.plotItems = []
        self.locked = False

        self.initializePlots()
        self.plotFiltered()
        self.applyImpedanceFile(impedanceFile)

        self.defaultHeight = 10000
        self.setDefaultHeight()

    def setDefaultHeight(self):
        self.resize(self.width(), self.defaultHeight)

    def initializePlots(self):
        for i in range(self.nchannels):
            row, col, willowChan = subplotIndex2rowColChan(i, self.probeMap, self.shank)
            plotItem = ClickablePlotItem(self.dataset, willowChan, row, col)
            self.addItem(plotItem)
            self.plotItems.append(plotItem)
            if i>=1: # link all plots together # TODO better way?
                plotItem.setXLink(self.plotItems[i-1])
                plotItem.setYLink(self.plotItems[i-1])
            self.locked = True
            if (i+1)%self.ncols==0:
                self.nextRow()

    def applyImpedanceFile(self, impedanceFile):
        self.impedanceFile = str(impedanceFile) if impedanceFile else False
        if self.impedanceFile:
            f = h5py.File(self.impedanceFile)
            impedanceMap = f['impedanceMeasurements']
            for plotItem in self.plotItems:
                willowChan = plotItem.chan
                impedance = impedanceMap[willowChan]
                if ((impedance > 1e6) or (impedance < 1e5)): # tweak this range as neeeded
                    if self.filtered:
                        plotItem.plotFiltered(dim=True)
                    else:
                        plotItem.plotRaw(dim=True)
                plotItem.setTitle(title='Row %d, Col %d, Chan %d, Z = %.0f k' %
                                    (plotItem.row, plotItem.col, willowChan, impedance/1000.))

    def toggleFiltered(self, filtered):
        if filtered:
            self.plotFiltered()
        else:
            self.plotRaw()

    def plotRaw(self):
        for plotItem in self.plotItems:
            plotItem.plotRaw()
        self.filtered = False

    def plotFiltered(self):
        for plotItem in self.plotItems:
            plotItem.plotFiltered()
        self.filtered = True

    def toggleAxes(self, axes):
        for plotItem in self.plotItems:
            plotItem.showAxis('left', show=axes)
            plotItem.showAxis('bottom', show=axes)

    def toggleLock(self, lock):
        if lock:
            for i,plotItem in enumerate(self.plotItems):
                if i>=1: # link all plots together, round-robin (is there a better way?)
                    plotItem.setXLink(self.plotItems[i-1])
                    plotItem.setYLink(self.plotItems[i-1])
        else:
            for plotItem in self.plotItems:
                plotItem.setXLink(None)
                plotItem.setYLink(None)
        self.locked = lock

    def setDefaultRange(self, filtered=True):
        self.setDefaultHeight()
        dataMin = self.dataset.slice_filtered_min if filtered else self.dataset.slice_min
        dataMax = self.dataset.slice_filtered_max if filtered else self.dataset.slice_max
        if self.locked:
            self.plotItems[0].setXRange(self.dataset.timeMin, self.dataset.timeMax)
            self.plotItems[0].setYRange(dataMin, dataMax, padding=0.9)
        else:
            for plotItem in self.plotItems:
                plotItem.setXRange(self.dataset.timeMin, self.dataset.timeMax)
                plotItem.setYRange(dataMin, dataMax, padding=0.9)

    def setImpedanceFile(self, impedanceFile):
        pass

    def wheelEvent(self, ev):
        # this overrides the wheelEvent behavior
        if ev.modifiers() == QtCore.Qt.ControlModifier:
            return pg.GraphicsLayoutWidget.wheelEvent(self, ev)
        elif ev.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            return pg.GraphicsLayoutWidget.wheelEvent(self, ev)
        else:
            ev.ignore() # propagate event to parent (scrollzoompanel)

class ShankPlotWindow(QtGui.QWidget):

    def __init__(self, dataset, probeMap, shank):
        QtGui.QWidget.__init__(self)

        # look for impedance files in the snapshot directory
        snapshotFilename = dataset.filename
        snapshotDir = os.path.dirname(snapshotFilename)
        impedanceFiles = glob.glob(os.path.join(snapshotDir, 'impedance*.h5'))
        if len(impedanceFiles) > 0:
            impedanceFile = impedanceFiles[-1] # most recent impedance measurement is used
        else:
            impedanceFile = False

        # filter data, find min and max for *this shank's channels only*
        shankChannels = []
        for item in probeMap:
            if item[0] == shank: shankChannels.append(probeMap[item])
        dataset.importSlice(chans=shankChannels)
        dataset.filterSlice()

        self.multiPlotWidget = MultiPlotWidget(dataset, probeMap, shank, impedanceFile)

        self.controlPanel = ControlPanel(dataset, impedanceFile)
        self.scrollZoomPanel = ScrollZoomPanel(self.multiPlotWidget)

        # signal connections
        self.controlPanel.filterToggled.connect(self.multiPlotWidget.toggleFiltered)
        self.controlPanel.lockToggled.connect(self.multiPlotWidget.toggleLock)
        self.controlPanel.axesToggled.connect(self.multiPlotWidget.toggleAxes)
        self.controlPanel.defaultSelected.connect(self.multiPlotWidget.setDefaultRange)
        self.controlPanel.impedanceFileSelected.connect(self.multiPlotWidget.applyImpedanceFile)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.controlPanel)
        layout.addWidget(self.scrollZoomPanel)
        self.setLayout(layout)

        self.setWindowTitle('Shank %d (%s)' % (shank, dataset.filename))
        self.setWindowIcon(QtGui.QIcon('../lib/img/leaflabs_logo.png'))
        self.showMaximized()

    def keyPressEvent(self, event):
        if event.modifiers() == QtCore.Qt.ControlModifier:
            if event.key() == QtCore.Qt.Key_Equal:
                self.scrollZoomPanel.verticalZoom(120)
            elif event.key() == QtCore.Qt.Key_Minus:
                self.scrollZoomPanel.verticalZoom(-120)

if __name__=='__main__':
    if len(sys.argv) < 3:
        print 'Usage: ./ShankPlot.py <snapshot_filename.h5> <probeMap_level2.p> [shank]'
        sys.exit(1)
    else:
        snapshot_filename = sys.argv[1]
        probeMap_filename = sys.argv[2]
        if len(sys.argv)==3:
            shank = 0
        else:
            shank = int(sys.argv[3])

    dataset = WillowDataset(snapshot_filename)

    probeMap = pickle.load(open(probeMap_filename, 'rb')) # (shank, col, row) : willowChan


    ####

    app = QtGui.QApplication(sys.argv)
    mainWindow = ShankPlotWindow(dataset, probeMap, shank)
    mainWindow.show()
    app.exec_()
