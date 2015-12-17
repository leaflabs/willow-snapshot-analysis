#!/usr/bin/python

import sys
import numpy as np

if len(sys.argv) < 3:
    print 'Usage: $ ./probeMap_converter.py <infile.txt> <outfile.npy>'
else:
    infile = sys.argv[1]
    outfile = sys.argv[2]
    fileArray = np.loadtxt(infile, dtype=int)
    probeMap = np.zeros((64, 2), dtype=int)
    for chan,shank,row,col in fileArray:
        probeMap[row-1, col-1] = chan-1 # justin's files are 1-indexed
    np.save(outfile, probeMap)
