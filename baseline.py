import sys
import numpy as np
import util

idxdict = {}
def loadidx(f):
    for line in f:
        idx, num = line.split('\t')
        idxdict[idx] = num
    
place = {}

def loadorder(f):
    for line in f:
        info = line.split('\t')
        driver = info[1]
        start = info[3]
        dt = util.convert_ts(info[-1])
        if start not in place:
            place[start] = {}
        if dt not in place[start]:
            place[start][dt] = np.array([0, 0])
        place[start][dt][0] += 1
        if driver == 'NULL':
            place[start][dt][1] += 1

if __name__ == '__main__':
    test_order = open(sys.argv[1]).read().split('\n')[:-1]
    idx = open(sys.argv[2]).read().split('\n')[:-1]
    loadidx(idx)
    loadorder(test_order)
    test_date = open(sys.argv[3]).read().split('\n')[1:-1]
    w = open('baseline.csv', 'w')
    for dt in test_date:
        dtinfo = dt.split('-')
        for p in place.keys():
            totalnum = 0
            weight = [0.5, 0.3, 0.2]
            for i in range(1, 4):
                newdt = int(dtinfo[-1]) - i
                newdt = '-'.join(dtinfo[0:-1]) + '-' + str(newdt)
                skipnum = 0
                if newdt in place[p]:
                    skipnum = place[p][newdt][1]
                totalnum += weight[i-1] * skipnum
            w.write(idxdict[p] + ',' + dt + ',' + str(totalnum) + '\n')
    w.close()
        #print dt
