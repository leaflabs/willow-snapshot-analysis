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

    def __init__(self, dataset, willowChan):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset
        self.chan = willowChan

        dataset.filterData(channelList=[self.chan])
        dataset.detectSpikes(channelList=[self.chan], thresh='auto')

        self.spikeLines = None
        self.hline = None

        self.mplPanel = self.createMplPanel()
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.mplPanel)
        self.layout.addWidget(self.toolbar)
        self.setLayout(self.layout)

        self.plotData()
        self.refreshSpikes()

        self.setWindowTitle('Spike Scope: Channel %d (%s)' % (self.chan,
                            self.dataset.filename))
        self.setWindowIcon(QtGui.QIcon('../lib/img/leaflabs_logo.png'))

    def on_click(self, event):
        if (event.inaxes == self.axes_chanPlot):
            if event.button == 2: # middle-click
                self.refreshSpikes(thresh='auto')
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
                    self.dataset.data_uv_filtered[self.chan,:], color='#8fdb90')
        self.canvas.draw()

    def refreshSpikes(self, thresh='auto'):
        if self.spikeLines:
            self.spikeLines.remove()
        if self.hline:
            self.hline.remove()
        self.dataset.detectSpikes(channelList=[self.chan], thresh=thresh)
        self.thresh = self.dataset.spikeThresholds[self.chan]
        xlim = self.axes_chanPlot.get_xlim()
        ylim = self.axes_chanPlot.get_ylim()
        self.spikeLines = self.axes_chanPlot.vlines(self.dataset.spikeTimes[self.chan],
                                    ylim[0], ylim[1], colors='#9933ff') 
        self.hline, = self.axes_chanPlot.plot(xlim, 2*[self.thresh], color='y')
        self.doSpikeScope()

    def doSpikeScope(self):
        self.axes_spikeScope.clear()
        self.axes_spikeScope.set_title('Spike Scope: %d Threshold Crossings'
                                        % self.dataset.nspikes[self.chan],
                                        fontsize=12)
        indices = self.dataset.spikeIndices[self.chan]
        for i in indices:
            try:
                tmpRange = np.arange(i-30, i+30, dtype='int')
                self.axes_spikeScope.plot((tmpRange-i)/30.,
                    self.dataset.data_uv_filtered[self.chan, tmpRange])
            except IndexError:
                pass # ignore spikes that are within 30 samples of the data limits
            self.axes_spikeScope.set_xlabel('ms')
            self.axes_spikeScope.set_ylabel('uV')
        self.canvas.draw()

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    filename = str(QtGui.QFileDialog.getOpenFileName(None, 'Select Data File', '/home/chrono/leafyles/neuro'))
    if filename:
        dataset = WillowDataset(filename, [0,29999])
        dataset.importData()
        spikeScopeWindow = SpikeScopeWindow(dataset, 166)
        spikeScopeWindow.show()
        app.exec_()
