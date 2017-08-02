#!/usr/bin/python

from PyQt4 import QtCore, QtGui
import numpy as np
import sys

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from WillowDataset import WillowDataset

class SpikeScopeWindow(QtGui.QWidget):

    def __init__(self, filename, willowChan):
        QtGui.QWidget.__init__(self)
        self.dataset = WillowDataset(filename)
        self.chan = willowChan

        self.dataset.importSlice(chans=[self.chan])
        self.dataset.filterSlice()
        self.dataset.detectSpikesSlice()
        self.slice_idx = self.dataset.chan2slice_idx[self.chan]

        self.spikeLines = None
        self.hline = None

        self.mplPanel = self.createMplPanel()
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.mplPanel)
        self.layout.addWidget(self.toolbar)
        self.setLayout(self.layout)

        self.refreshSpikes()
        self.plotData()

        self.setWindowTitle('Spike Scope: Channel %d (%s)' % (self.chan,
                            self.dataset.filename))
        self.setWindowIcon(QtGui.QIcon('../lib/img/leaflabs_logo.png'))

    def on_click(self, event):
        if (event.inaxes == self.axes_chanPlot):
            if event.button == 2: # middle-click
                self.refreshSpikes()
            elif event.button == 3: # right-click
                self.refreshSpikes(thresh=event.ydata)

    def createMplPanel(self):
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.mpl_connect('button_press_event', self.on_click)

        self.axes_chanPlot = self.fig.add_subplot(211)
        self.axes_chanPlot.set_title('Filtered Data: Right Click to Set '
                                     'Threshold, Middle Click for Default',
                                      fontsize=12)
        self.axes_spikeScope = self.fig.add_subplot(212)

        self.fig.subplots_adjust(hspace=0.3)

        mplPanel = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        mplPanel.setLayout(layout)

        return mplPanel

    def plotData(self):
        self.axes_chanPlot.set_axis_bgcolor('k')
        self.axes_chanPlot.plot(self.dataset.time_ms,
                    self.dataset.slice_filtered[self.slice_idx,:], color='#8fdb90')
        self.canvas.draw()

    def refreshSpikes(self, thresh=None):
        if self.spikeLines:
            self.spikeLines.remove()
        if self.hline:
            self.hline.remove()
        self.dataset.detectSpikesSlice(thresh=thresh)
        spike = self.dataset.spikes[self.slice_idx]
        xlim = self.axes_chanPlot.get_xlim()
        ylim = self.axes_chanPlot.get_ylim()
        self.spikeLines = self.axes_chanPlot.vlines(spike['times'],
                                    ylim[0], ylim[1], colors='#9933ff') 
        self.hline, = self.axes_chanPlot.plot(xlim, 2*[spike['thresh']], color='y')
        self.doSpikeScope()

    def doSpikeScope(self):
        self.axes_spikeScope.clear()
        spike = self.dataset.spikes[self.slice_idx]
        self.axes_spikeScope.set_title('Spike Scope: %d Threshold Crossings'
                                        % spike['nspikes'], fontsize=12)
        for i in spike['indices']:
            try:
                tmpRange = np.arange(i-30, i+30, dtype='int')
                self.axes_spikeScope.plot((tmpRange-i)/30.,
                    self.dataset.slice_filtered[self.slice_idx, tmpRange])
            except IndexError:
                pass # ignore spikes that are within 30 samples of the data limits
            self.axes_spikeScope.set_xlabel('ms')
            self.axes_spikeScope.set_ylabel('uV')
        self.canvas.draw()

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    filename = str(QtGui.QFileDialog.getOpenFileName(None, 'Select Data File', '/home/chrono/leafyles/neuro'))
    if filename:
        spikeScopeWindow = SpikeScopeWindow(filename, 166)
        spikeScopeWindow.show()
        app.exec_()
