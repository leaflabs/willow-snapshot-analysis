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

def willowChanFromSubplotIndex(subplotIndex, probeMap, shank):
    # here's some mangling that's necessary b.c. pyqtgraph plots subplots
    #   in column-major order (?), for some reason
    chansPerRow = max([key[2] for key in probeMap.keys() if type(key) == tuple]) + 1
    subplotRow = subplotIndex // chansPerRow
    subplotCol = subplotIndex % chansPerRow
    willowChan = probeMap[shank, subplotRow, subplotCol]
    return willowChan

####
# main widget classes

class HelpWindow(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)

        usageText = ("<center><b>Usage:</b></center>"
                    "<ul>"
                    "<li>Mousewheel scrolls through probe-mapped channels</li>"
                    "<li>Ctrl-Plus and Ctrl-Minus expands or contracts the plot canvas vertically</li>"
                    "<li>Ctrl-Mousewheel over a plot zooms isometrically</li>"
                    "<li>Ctrl-Mousewheel over an axis zooms in that dimension</li>"
                    "<li>By default, all plot axes are locked together. To unlock them, uncheck the 'Lock Plots Together' box in the control panel</li>"
                    "<li>Double-click on a plot to open a SpikeScope window for that channel</li>"
                    "<li>Channel numbers are 0-indexed, and in reference to the 1024-channel Willow dataspace</li>"
                    "<li>y-axes have units of microVolts (uV), x-axes have units of milliseconds (ms)</li>"
                    "<li>You may wish to adjust some parameters, like the channel offset or probemap file, in the CONFIG section of the main script</li>"
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
    spikesToggled = QtCore.pyqtSignal(bool)
    axesToggled = QtCore.pyqtSignal(bool)
    lockToggled = QtCore.pyqtSignal(bool) 
    defaultSelected = QtCore.pyqtSignal(bool) 

    def __init__(self, dataset):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset

        self.filterCheckbox = QtGui.QCheckBox('Display Filtered')
        self.filterCheckbox.setChecked(True)
        self.filterCheckbox.stateChanged.connect(self.toggleFiltered)

        self.spikeDetectCheckbox = QtGui.QCheckBox('Display Spikes')
        self.spikeDetectCheckbox.stateChanged.connect(self.toggleSpikes)

        self.axesCheckbox = QtGui.QCheckBox('Display Axes')
        self.axesCheckbox.setChecked(True)
        self.axesCheckbox.stateChanged.connect(self.toggleAxes)

        self.lockCheckbox = QtGui.QCheckBox('Lock Plots Together')
        self.lockCheckbox.setChecked(True)
        self.lockCheckbox.stateChanged.connect(self.toggleLock)

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
        self.layout.addWidget(self.defaultButton)
        self.layout.addWidget(self.helpButton)
        self.setLayout(self.layout)

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

    def toggleSpikes(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.spikesToggled.emit(self.spikeDetectCheckbox.isChecked())
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

    def __init__(self, *args, **kwargs):
        pg.PlotItem.__init__(self, *args, **kwargs)
        self.chan = -1

    def setChannel(self, chan, **kwargs):
        self.chan = chan
        if 'impedance' in kwargs:
            impedance = kwargs['impedance']
            self.setTitle(title='Ch %d, Z = %.2f k' % (self.chan, impedance/1000.))
        else:
            self.setTitle(title='Channel %d' % self.chan)

    def setDataset(self, dataset):
        self.dataset = dataset

    def mouseDoubleClickEvent(self, event):
        self.spikeScopeWindow = SpikeScopeWindow(self.dataset, self.chan)
        self.spikeScopeWindow.show()

class MultiPlotWidget(pg.GraphicsLayoutWidget):

    def __init__(self, dataset, probeMap, shank, impedanceMap):
        pg.GraphicsLayoutWidget.__init__(self)
        self.dataset = dataset
        self.probeMap = probeMap
        self.shank = shank
        self.impedanceMap = impedanceMap

        self.nchannels = self.probeMap['ncols']*self.probeMap['nrows']

        self.plotItems = []
        self.locked = False

        self.initializePlots()
        self.plotFiltered()

        self.defaultHeight = 10000
        self.setDefaultHeight()

    def setDefaultHeight(self):
        self.resize(self.width(), self.defaultHeight)

    def initializePlots(self):
        for i in range(self.nchannels):
            willowChan = willowChanFromSubplotIndex(i, self.probeMap, self.shank)
            plotItem = ClickablePlotItem()
            if self.impedanceMap:
                plotItem.setChannel(willowChan, impedance=self.impedanceMap[willowChan])
            else:
                plotItem.setChannel(willowChan)
            plotItem.setDataset(self.dataset) # TODO better way?
            self.addItem(plotItem)
            self.plotItems.append(plotItem)
            if i>=1: # link all plots together # TODO better way?
                plotItem.setXLink(self.plotItems[i-1])
                plotItem.setYLink(self.plotItems[i-1])
            self.locked = True
            if (i+1)%2==0:
                self.nextRow()

    def toggleFiltered(self, filtered):
        self.clearAll()
        if filtered:
            self.plotFiltered()
        else:
            self.plotRaw()

    def toggleSpikes(self, spikes):
        if spikes:
            pass
        else:
            pass

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

    def overlaySpikes(self):
        for i,plot in enumerate(self.plotItems):
            willowChan = willowChanFromSubplotIndex(i, self.probeMap, self.shank)
            plot.addLine(x=self.dataset.spikeTimes[willowChan][0])
            #for spikeTime in self.dataset.spikeTimes[willowChan]:
            #    plot.addLine(x=spikeTime)

    def removeSpikes(self):
        pass # TODO

    def clearAll(self):
        for plotItem in self.plotItems:
            plotItem.clear()

    def plotFiltered(self):
        for i,plot in enumerate(self.plotItems):
            willowChan = willowChanFromSubplotIndex(i, self.probeMap, self.shank)
            plot.plot(x=self.dataset.time_ms, y=self.dataset.data_uv_filtered[willowChan,:],
                        pen=(143,219,144))
            plot.setYRange(self.dataset.dataMin_filtered, self.dataset.dataMax_filtered, padding=0.9)

    def plotRaw(self):
        for i,plot in enumerate(self.plotItems):
            willowChan = willowChanFromSubplotIndex(i, self.probeMap, self.shank)
            plot.plot(x=self.dataset.time_ms, y=self.dataset.data_uv[willowChan,:],
                        pen=(143,219,144))
            plot.setYRange(self.dataset.dataMin, self.dataset.dataMax, padding=0.9)

    def setDefaultRange(self, filtered=True):
        self.setDefaultHeight()
        dataMin = self.dataset.dataMin_filtered if filtered else self.dataset.dataMin
        dataMax = self.dataset.dataMax_filtered if filtered else self.dataset.dataMax
        if self.locked:
            self.plotItems[0].setXRange(self.dataset.timeMin, self.dataset.timeMax)
            self.plotItems[0].setYRange(dataMin, dataMax, padding=0.9)
        else:
            for plotItem in self.plotItems:
                plotItem.setXRange(self.dataset.timeMin, self.dataset.timeMax)
                plotItem.setYRange(dataMin, dataMax, padding=0.9)

    def wheelEvent(self, ev):
        # this overrides the wheelEvent behavior
        if ev.modifiers() == QtCore.Qt.ControlModifier:
            return pg.GraphicsLayoutWidget.wheelEvent(self, ev)
        else:
            ev.ignore() # propagate event to parent (scrollzoompanel)

class ShankPlotWindow(QtGui.QWidget):

    def __init__(self, dataset, probeMap, shank, impedanceMap):
        QtGui.QWidget.__init__(self)

        # filter data, find min and max for *this shank's channels only*
        shankChannels = []
        for item in probeMap:
            if item[0] == shank: shankChannels.append(probeMap[item])
        dataset.filterData(channelList=shankChannels)
        dataset.dataMin = np.min(dataset.data_uv[shankChannels,:])
        dataset.dataMax = np.max(dataset.data_uv[shankChannels,:])
        dataset.dataMin_filtered = np.min(dataset.data_uv_filtered[shankChannels,:])
        dataset.dataMax_filtered = np.max(dataset.data_uv_filtered[shankChannels,:])

        self.multiPlotWidget = MultiPlotWidget(dataset, probeMap, shank, impedanceMap)

        self.controlPanel = ControlPanel(dataset)
        self.scrollZoomPanel = ScrollZoomPanel(self.multiPlotWidget)

        # signal connections
        self.controlPanel.filterToggled.connect(self.multiPlotWidget.toggleFiltered)
        self.controlPanel.lockToggled.connect(self.multiPlotWidget.toggleLock)
        self.controlPanel.spikesToggled.connect(self.multiPlotWidget.toggleSpikes)
        self.controlPanel.axesToggled.connect(self.multiPlotWidget.toggleAxes)
        self.controlPanel.defaultSelected.connect(self.multiPlotWidget.setDefaultRange)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.controlPanel)
        layout.addWidget(self.scrollZoomPanel)
        self.setLayout(layout)

        self.setWindowTitle('Shank %d' % shank)
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

    dataset = WillowDataset(snapshot_filename, -1)
    dataset.importData()

    probeMap = pickle.load(open(probeMap_filename, 'rb')) # (shank, col, row) : willowChan

    snapshot_dir = os.path.dirname(snapshot_filename)
    impedanceFiles = glob.glob(os.path.join(snapshot_dir, 'impedance*.h5'))
    if len(impedanceFiles) > 0:
        impedance_filename = impedanceFiles[0]
        f = h5py.File(impedance_filename)
        impedanceMap = f['impedanceMeasurements']
    else:
        impedanceMap = False

    print 'impedanceMap = ', impedanceMap

    ####

    app = QtGui.QApplication(sys.argv)
    mainWindow = ShankPlotWindow(dataset, probeMap, shank, impedanceMap)
    mainWindow.show()
    app.exec_()
