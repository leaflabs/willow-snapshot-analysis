import os
from PyQt4 import QtCore, QtGui

class PathButton(QtGui.QPushButton):

    def __init__(self, prompt, start_dir):
        QtGui.QPushButton.__init__(self, start_dir)

        self.start_dir = start_dir
        self.prompt = prompt
        self.clicked.connect(self.browseForPath)

    def browseForPath(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, self.prompt, self.start_dir)
        if filename:
            self.setText(filename)

class PlaybackDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(PlaybackDialog, self).__init__(parent)

        self.chipNumberLine = QtGui.QLineEdit('0')
        self.chipNumberLine.setValidator(QtGui.QIntValidator(0,31,self))

        self.xrangeLine = QtGui.QLineEdit('1000')
        self.xrangeLine.setValidator(QtGui.QDoubleValidator(1,100000,1,self))

        self.refreshRateLine = QtGui.QLineEdit('20')
        self.refreshRateLine.setValidator(QtGui.QIntValidator(2,60,self))

        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        self.probeMapPath = PathButton('Select probe map file', 
            os.path.dirname(os.path.realpath(__file__)))
        self.probeMapPath.setEnabled(False)
        self.probeMapCheckbox = QtGui.QCheckBox('Use probe map data')
        self.probeMapCheckbox.setCheckState(QtCore.Qt.Unchecked)
        self.probeMapCheckbox.toggled.connect(lambda s: self.probeMapPath.setEnabled(s))

        layout = QtGui.QGridLayout()
        layout.addWidget(QtGui.QLabel('Chip Number:'), 0,0, 1,1)
        layout.addWidget(self.chipNumberLine, 0,1, 1,2)
        layout.addWidget(QtGui.QLabel('Maximal displayed x-range (ms):'), 2,0, 1,1)
        layout.addWidget(self.xrangeLine, 2,1, 1,1)
        layout.addWidget(QtGui.QLabel('Refresh Rate (Hz):'), 3,0, 1,1)
        layout.addWidget(self.refreshRateLine, 3,1, 1,2)
        layout.addWidget(self.probeMapCheckbox, 4,0, 1,2)
        layout.addWidget(self.probeMapPath, 4,1, 1,2)
        layout.addWidget(self.dialogButtons, 5,1, 1,2)

        self.setLayout(layout)
        self.setWindowTitle('Playback Window Parameters')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.resize(500,100)


    def getParams(self):
        params = {}
        params['chip'] = int(self.chipNumberLine.text())
        params['xrange'] = int(self.xrangeLine.text())
        params['refreshRate'] = int(self.refreshRateLine.text())
        if self.probeMapCheckbox.checkState():
            params['probeMapPath'] = str(self.probeMapPath.text())
        else:
            params['probeMapPath'] = None
        return params
