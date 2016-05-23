import sys
import numpy as np
import util
import math

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

vali = set([])

def loadvali(f):
    for line in f:
        vali.add(line)

#caculate mape
#input dict{place:[time,true,predict]}
def mape(f):
    totalinv = len(f)
    ts = 0
    result = 0
    avg = 0
    for p in f:
        if len(f[p]) > ts:
            ts = len(f[p])
        for tslot in f[p]:
            #print tslot
            if tslot[1] == 0:
                continue
            avg += tslot[1]
            result += abs(tslot[1] - tslot[2]) / (tslot[1] + .0)
    result = result / (totalinv * ts)
    print avg / (totalinv * ts + 0.0)
    return result

if __name__ == '__main__':
    test_order = open(sys.argv[1]).read().split('\n')[:-1]
    idx = open(sys.argv[2]).read().split('\n')[:-1]
    loadidx(idx)
    loadorder(test_order)
    loadvali(open(sys.argv[3]).read().split('\n')[:-1])
    testdict = {}
    for v in vali:
        prev = '-'.join(v.split('-')[:-1]) + '-' + str(int(v.split('-')[-1]) - 1)
        for p in place:
            if p not in testdict:
                testdict[p] = []
            truep = 0
            prep = 1
            if prev in place[p]:
                prep = (place[p][prev][1]) / 2.0
                #if prep > 10:
                #    prep = prep * 2
            if prep < 1:
                prep = 1
            if v not in place[p]:
                continue
            testdict[p].append((v, place[p][v][1], prep))
            if place[p][v][1] > 0 and abs((prep - place[p][v][1]) / (place[p][v][1] + 0.0)) > 0.5 and prev in place[p]:
                print p + ' ' + str(place[p][v][1]) + ' ' + str(prep) + ' ' + str(place[p][prev][1])
    print mape(testdict)
            
#     test_date = open(sys.argv[3]).read().split('\n')[1:-1]
#     w = open('baseline.csv', 'w')
#     for dt in test_date:
#         dtinfo = dt.split('-')
#         for p in place.keys():
#             totalnum = 0
#             for i in range(1, 2):
#                 newdt = int(dtinfo[-1]) - i
#                 newdt = '-'.join(dtinfo[0:-1]) + '-' + str(newdt)
#                 skipnum = 0
#                 if newdt in place[p]:
#                     skipnum = place[p][newdt][1]
#                 totalnum += 0.5 * skipnum
#             if totalnum < 1:
#                 totalnum = 1.0
#             w.write(idxdict[p] + ',' + dt + ',' + str(2) + '\n')
#     w.close()

