import numpy as np
import h5py
from PyQt4 import QtCore
import scipy.signal as signal

IMPORT_LIMIT_GB = 8
MAX_NSAMPLES = IMPORT_LIMIT_GB*5e5
MICROVOLTS_PER_COUNT = 0.195

def analyzeBuffer(buff):
    buffarray = np.array(buff)
    maxind = np.argmax(buffarray[:,1])
    return buff[maxind][0]

def threshold(indata, thresh=None):
    if thresh==None:
        print 'Threshold not defined, here is min mean and max:'
        print np.min(indata), np.mean(indata), np.max(indata)
    else:
        # next two lines make the algorithm agnostic of polarity (pos/neg)
        polarity = -1. if (thresh < 0) else 1.
        thresh = abs(thresh)
        # init buffers and counters
        recording = False
        buff = []
        stats = []
        nspikes = 0
        # run over the data
        for i,samp in enumerate(polarity*indata):
            if not recording:
                if samp>=thresh:
                    buff.append((i,samp))
                    recording = True
            else:
                if samp<thresh:
                    recording = False
                    stats.append(analyzeBuffer(buff))
                    nspikes += 1
                    buff = []
                else:
                    buff.append((i,samp))

        return stats, nspikes

class WillowImportError(Exception):
    pass

class WillowDataset(QtCore.QObject):
    """
    Willow Dataset Container Class
    Common format for passing data between import processes, plot windows, etc.
    """

    progressUpdated = QtCore.pyqtSignal(int)

    def __init__(self, filename, sampleRange):
        QtCore.QObject.__init__(self)
        self.filename = filename
        self.fileObject = h5py.File(self.filename)
        # the following test allows for backward-compatibility
        if 'wired-dataset' in self.fileObject:
            self.isOldLayout = True
            self.dset = self.fileObject['wired-dataset']
            # determine type based on header flag
            if (self.dset[0][0] & (1<<6)):
                self.type = 'snapshot'
            else:
                self.type = 'experiment'
        else:
            self.isOldLayout = False 
            self.dset = self.fileObject['channel_data']
            # determine type based on header flag
            if self.fileObject['ph_flags'][0] & (1<<6):
                self.type = 'snapshot'
            else:
                self.type = 'experiment'

        # define self.sampleRange and related temporal data
        if sampleRange==-1:
            if self.isOldLayout:
                self.nsamples = len(self.dset)
            else:
                self.nsamples = len(self.dset)//1024
            self.sampleRange = [0, self.nsamples-1]
        else:
            self.sampleRange = sampleRange
            self.nsamples = self.sampleRange[1] - self.sampleRange[0] + 1
            if self.isOldLayout:
                dsetMin = int(self.dset[0][1])
                dsetMax = int(self.dset[-1][1])
            else:
                dsetMin = int(self.fileObject['sample_index'][0])
                dsetMax = int(self.fileObject['sample_index'][-1])
            if self.type=='snapshot':
                # need to normalize because snapshots have random offsets
                dsetMax -= dsetMin
                dsetMin = 0
            if (self.sampleRange[0] < dsetMin) or (self.sampleRange[1] > dsetMax):
                raise IndexError('Error: sampleRange [%d, %d] out of range for dset: [%d, %d]'
                    % tuple(self.sampleRange+[dsetMin,dsetMax]))
        self.time_ms = np.arange(self.sampleRange[0], self.sampleRange[1]+1)/30.
        self.timeMin = np.min(self.time_ms)
        self.timeMax = np.max(self.time_ms)

        # other metadata
        if self.isOldLayout:
            self.boardID = self.dset.attrs['board_id'][0]
            if self.type=='experiment':
                self.cookie = self.dset.attrs['experiment_cookie'][0]
            else:
                self.cookie = None
            chipAliveMask = self.dset[0][2]
        else:
            self.boardID = self.fileObject.attrs['board_id'][0]
            if self.type=='experiment':
                self.cookie = self.fileObject.attrs['experiment_cookie'][0]
            else:
                self.cookie = None
            chipAliveMask = self.fileObject['chip_live'][0]
        self.chipList = [i for i in range(32) if (chipAliveMask & (0x1 << i))]

        # flags
        self.isImported = False
        self.isFiltered = [False]*1024
        self.data_uv_filtered = np.zeros((1024,self.nsamples), dtype='float')

        # spikedetection
        self.spikeThresholds = {}
        self.spikeIndices = {}
        self.nspikes = {}
        self.spikeTimes= {}

    def importData(self):
        if self.isOldLayout:
            if self.nsamples > MAX_NSAMPLES:
                raise WillowImportError
            self.data_raw = np.zeros((1024,self.nsamples), dtype='uint16')
            for i in range(self.nsamples):
                self.data_raw[:,i] = self.dset[self.sampleRange[0]+i][3][:1024]
                if (i%1000==0):
                    self.progressUpdated.emit(i)
        else:
            self.progressUpdated.emit(0)
            self.data_raw = np.array(self.fileObject['channel_data'][self.sampleRange[0]
                *1024:(self.sampleRange[1]+1)*1024], dtype='uint16').reshape(
                (self.nsamples, 1024)).transpose()
            self.data_aux = np.array(self.fileObject['aux_data'][self.sampleRange[0]
                *96:(self.sampleRange[1]+1)*96], dtype='uint16').reshape(
                (self.nsamples, 96)).transpose()
            self.sample_index = np.array(self.fileObject['sample_index'][self.sampleRange[0]:
                                self.sampleRange[1]+1])
            self.parseGPIO()
        self.progressUpdated.emit(self.nsamples)
        self.data_uv = (np.array(self.data_raw, dtype='float')-2**15)*MICROVOLTS_PER_COUNT
        self.dataMin = np.min(self.data_uv)
        self.dataMax = np.max(self.data_uv)
        self.limits = [self.timeMin, self.timeMax, self.dataMin, self.dataMax]
        self.isImported = True

    def parseGPIO(self):
        self.GPIOindices = np.where(self.sample_index % 15 == 11)[0]
        self.GPIOtimes = self.time_ms[self.GPIOindices]
        # GPIO gets copied into slot 1 for all 32 chips, so 1,4,7.. would all work
        GPIO_bitfield = self.data_aux[1, self.GPIOindices]
        self.GPIO = np.zeros((16,len(GPIO_bitfield)))
        for i in range(16):
            self.GPIO[i,:] = np.bool_(GPIO_bitfield & (1 << i))

    def filterData(self, channelList=range(1024)):
        lowcut = 300.
        highcut = 9500.
        fs = 3e4
        order = 5
        b, a = signal.butter(order, [lowcut*2./fs, highcut*2./fs], btype='band')
        for chan in channelList:
            if not self.isFiltered[chan]:
                self.data_uv_filtered[chan,:] = signal.filtfilt(b, a, self.data_uv[chan,:])
                self.isFiltered[chan] = True

    def detectSpikes(self, channelList=range(1024), thresh='auto'):
        for i in channelList: 
            tmpChannel = self.data_uv_filtered[i,:]
            if thresh=='auto':
                thresh = -4.5*np.median(np.abs(tmpChannel))/0.6745  # from Justin
            self.spikeIndices[i], self.nspikes[i] = threshold(tmpChannel, thresh)
            self.spikeTimes[i] = self.time_ms[self.spikeIndices[i]]
            self.spikeThresholds[i] = thresh

    def applyCalibration(self, calibrationFile):
        self.calibrationFile = calibrationFile
        self.impedance = np.load(str(self.calibrationFile))
        self.data_cal = np.zeros((1024, self.nsamples), dtype='float')
        for (i, imp) in enumerate(self.impedance):
            print i
            if imp>0:
                self.data_cal[i,:] = self.data_uv[i,:]*imp
            # else just leave it at zero

if __name__=='__main__':
    filename = '/home/chrono/neuro/data/hasenstaub/20151121/exp8_clicks_snapshot_20151121-191941.h5'
    dataset = WillowDataset(filename, [0,30000-1])
    dataset.importData()
    import matplotlib.pyplot as plt
    for i in range(16):
        plt.plot(dataset.GPIO[i])
        plt.show()
