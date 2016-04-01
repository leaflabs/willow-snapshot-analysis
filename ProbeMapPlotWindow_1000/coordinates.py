#!/usr/bin/python

import sys

chipchan2ffcCable = {
    28:0,
    23:1,
    29:2,
    22:3,
    30:4,
    21:5,
    31:6,
    20:7,
    27:8,
    19:9,
    26:10,
    18:11,
    25:12,
    17:13,
    24:14,
    16:15,
    #(ref):16,
    15:17,
    7:18,
    14:19,
    6:20,
    13:21,
    5:22,
    12:23,
    4:24,
    11:25,
    0:26,
    10:27,
    1:28,
    9:29,
    2:30,
    8:31,
    3:32
}

def ffcCable2probeFFC(ffcCable):
    return 33 - ffcCable # interdigitated

def willowChan2chipChan(willowChan):
    chip = willowChan // 32
    chipchan = willowChan % 32
    return (chip, chipchan)

ffcCable2probeFFC(chipchan2ffcCable[chipchan])

def willowChan2ffc(willowChan):
    chipChan = willowChan
    if willowChan < 512:
        row = 3 - (willowChan // 128)
        col = willowChan % 128
        # note: dave's netlists are 1-indexed
        connector = row*4 + (col // 32) + 1
        pin = (col % 32) + 1
        ffc = (connector, pin)
    else:
        willowChan512  = willowChan - 512
        row = 3 - (willowChan512 // 128)
        col = willowChan % 128
        # rows and columns are backwards for connector ordering here
        row_bw = 3 - row
        col_bw = 127 - col
        # note: dave's netlists are 1-indexed
        print row_bw, col_bw
        connector = row_bw*4 + (col_bw // 32) + 17
        pin = (col % 32) + 1
        ffc = (connector, pin)
    return ffc

def ffc2wirebondDave(ffc):
    # ffc is a tuple, e.g. (21,32) = J21.32
    wirebondDave = -1 # todo
    return wirebondDave

def wirebondDave2wirebondJorg(wirebondDave):
    wirebondJorg = (-1,-1) # todo
    pass

def wirebondJorg2pad():
    pass

if __name__ == '__main__':
    # test
    #willowChan = int(sys.argv[1])
    #print 'willowChan = %d' % willowChan
    #print 'ffc = (%d, %d)' % willow2ffc(willowChan)
    for willowChan in range(1024):
        print willowChan, willow2ffc(willowChan)
