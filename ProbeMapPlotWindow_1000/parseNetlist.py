#!/usr/bin/python

import sys, pickle

def run(filename):
    mapping = {}
    f = open(filename, 'r')
    for l in f:
        if l[0] != '*':
            words = l.split()
            if len(words) == 2:
                ffcCode = words[0]
                wirebondDaveCode = words[1]
                if ffcCode[:1]=='J' and wirebondDaveCode[:4]=='J33.':
                    ffcList = ffcCode[1:].split('.')
                    ffc = (int(ffcList[0]), int(ffcList[1]))
                    mapping[ffc] = int(wirebondDaveCode[4:])
    print mapping
    print len(mapping)

if __name__=='__main__':
    if (len(sys.argv))<2:
        print 'Usage:'
        print '$ ./parseNetlist.py <filename.txt>'
        sys.exit(1)
    else:
        run(sys.argv[1])
