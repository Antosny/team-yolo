import numpy as np
import pandas as pd
import sys
import os
import util
from datetime import datetime
from sklearn.linear_model import *
from sklearn.ensemble import *

writefeature=True
testset = set()
place_map = {}

def load_map(path):
    a = open(path).read().split('\n')[1:-1]
    for line in a:
        place, idx = line.split(',')
        place_map[place] = int(idx)

def load_test(path):
    a = open(path).read().split('\n')[:-1]
    for line in a:
        testset.add(util.ts_idx(line))
    return testset

def load_data(order):
    return pd.read_csv(order)


def is_test_data(ts):
    for i in range(0, 2):
        if int(ts) + i in testset:
            return True
    return False

def split_data(order, vali = True):
    if vali:
        order['test'] = order['tsidx'].apply(is_test_data)
        traindata = order[order['test'] == False]
        testdata = order[order['test'] == True]
        traindata.index = traindata[['start_district_hash', 'tsidx']]
        idx = pd.MultiIndex.from_tuples(traindata.index)
        traindata.index = idx
        testdata.index = testdata[['start_district_hash', 'tsidx']]
        idx = pd.MultiIndex.from_tuples(testdata.index)
        testdata.index = idx
        return traindata, testdata
    else:
        traindata = order
        traindata.index = traindata[['start_district_hash', 'tsidx']]
        idx = pd.MultiIndex.from_tuples(traindata.index)
        traindata.index = idx
        return traindata

def ts_feature(ts):
    ts = util.idx_ts(int(ts))
    tsinfo = ts.split('-')
    tshour = (int(tsinfo[-1]) - 1) / 6
    tsmin = 10 * ((int(tsinfo[-1]) - 1) % 6)
    tsstr = '-'.join(tsinfo[:-1]) + '-' + str(tshour) + '-' + str(tsmin)
    dt = datetime.strptime(tsstr, '%Y-%m-%d-%H-%M')
    feature = []
    weekend = 0
    if dt.isoweekday() < 6:
        weekend = 1
    #feature.append(weekend)
    feature.append(dt.isoweekday())
    feature.append(dt.hour)
    feature.append(dt.minute)
    return feature

def transform(data, istrain = True):
    x = []
    y = []
    idx = []
    weight = []
    datadict = data.to_dict('index')
    if istrain:
        for place, ts in datadict:
            if place not in place_map:
                continue
            if int(ts) <= 576:
                continue
            label = float(datadict[(place, ts)]['gap'])
            y.append(label)
            x.append(get_feature(place, ts, datadict))
            idx.append([place, ts])
            if label == 0:
                weight.append(0.001)
            else:
                weight.append(1./label)
    else:
        for place in place_map:
            for ts in testset:
                y.append(-1)
                x.append(get_feature(place, ts, datadict))
                idx.append([place, ts])

    return x, y, np.array(idx), weight



def get_feature(place, ts, datadict):
    f = []
    f.append(place_map[place])
    f += ts_feature(ts)
    #previous gap
    for i in range(1, 4):
        if i <= 5:
            if (place, ts - i) in datadict:
                f.append(datadict[(place, ts - i)]['gap'])
                f.append(datadict[(place, ts - i)]['call'])
                f.append(datadict[(place, ts - i)]['answer'])
            else:
                f.append(0)
                f.append(0)
                f.append(0)
        else:
            oldkey = (place, ts - i + 1)
            crtkey = (place, ts - i)
            g = 0
            c = 0
            a = 0
            if oldkey in datadict:
                g += datadict[oldkey]['gap']
                c += datadict[oldkey]['call']
                a += datadict[oldkey]['answer']
            if crtkey in datadict:
                g -= datadict[crtkey]['gap']
                c -= datadict[crtkey]['call']
                a -= datadict[crtkey]['answer']
            f.append(g)
            f.append(c)
            f.append(a)

                
    return f


def mape(y_true, y_pred, idx, istrain = False):
    lenplace = len(set(idx[:, 0]))
    if istrain:
        divider = lenplace * len(set(idx[:, 1])) * 1.
    else:
        divider = lenplace * len(testset) * 1.
    result_mape = 0.0
    placemape = {}
    for i in range(0, len(y_true)):
        place, ts = idx[i]
        if not istrain and int(ts) not in testset:
            continue
        if y_true[i] > 0:
            if place not in placemape:
                placemape[place] = 0.0
            result_mape += abs((y_true[i] - y_pred[i]) / (y_true[i] * 1.))
            placemape[place] += abs((y_true[i] - y_pred[i]) / (y_true[i] * 1.))
    for place in sorted(placemape.keys()):
        print place + ' mape:' + str(placemape[place] / (divider / lenplace))
    return result_mape / divider
    


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'usage: python flow.py vali|test params'
        sys.exit(1)
    gbrt = GradientBoostingRegressor(loss='lad', max_depth=8)
    if sys.argv[1] == 'vali':
        valipath = sys.argv[2]
        orderpath = sys.argv[3]
        load_test(valipath)
        load_map(sys.argv[4])
        traindata, testdata = split_data(load_data(orderpath), True)
        x_tr, y_tr, idx_tr, weight_tr = transform(traindata)
        #print idx_tr.keys()
        w = open('train.data', 'w')
        for i in range(0, len(weight_tr)):
           w.write(str(weight_tr[i]) + ':::' + str(y_tr[i]) + ':::' + '$'.join([str(x) for x in x_tr[i]]) + '\n')
        w.close()
        print '---------------'
        x_te, y_te, idx_te, weight_te = transform(testdata)
        #print idx_te.keys()
        w = open('test.data', 'w')
        for i in range(0, len(weight_te)):
           ts = int(idx_te[i][1])
           if ts not in testset:
               continue
           w.write(str(weight_te[i]) + ':::' + str(y_te[i]) + ':::' + '$'.join([str(x) for x in x_te[i]]) + '\n')
        w.close()
        print 'size of training:' + str(len(y_tr))
        print 'size of test:' + str(len(y_te))
        model = {}
        tr_pred = {}
        y_pred = {}
        gbrt.fit(x_tr, y_tr, sample_weight = weight_tr)
        tr_pred = gbrt.predict(x_tr)
        y_pred = gbrt.predict(x_te)
        print 'train mape:' + str(mape(y_tr, tr_pred, idx_tr, True))
        print 'validation mape:' + str(mape(y_te, y_pred, idx_te))
    if sys.argv[1] == 'test':
        testpath = sys.argv[2]
        orderpath = sys.argv[3]
        testorderpath = sys.argv[4]
        load_test(testpath)
        load_map(sys.argv[5])
        traindata = split_data(load_data(orderpath), False)
        testdata = split_data(load_data(testorderpath), False)
        x_tr, y_tr, idx_tr, weight_tr = transform(traindata)
        w = open('train.data.all', 'w')
        for i in range(0, len(weight_tr)):
           w.write(str(weight_tr[i]) + ':::' + str(y_tr[i]) + ':::' + '$'.join([str(x) for x in x_tr[i]]) + '\n')
        w.close()

        print '---------------'
        x_te, y_te, idx_te, weight_te = transform(testdata, False)
        w = open('test.data.all', 'w')
        for i in range(0, len(weight_te)):
           ts = int(idx_te[i][1])
           if ts not in testset:
               continue
           w.write(str(weight_te[i]) + ':::' + str(y_te[i]) + ':::' + '$'.join([str(x) for x in x_te[i]]) + '\n')
        w.close()

        print 'size of training:' + str(len(y_tr))
        print 'size of test:' + str(len(y_te))
        gbrt.fit(x_tr, y_tr, sample_weight = weight_tr)
        tr_pred = gbrt.predict(x_tr)
        y_pred = gbrt.predict(x_te)
        w = open(sys.argv[6], 'w')
        for i in range(0, len(idx_te)):
            place = str(place_map[idx_te[i][0]])
            ts = str(util.idx_ts(int(idx_te[i][1])))
            print place + ' ' + ts
            w.write(place + ',' + ts + ',' + str(max(y_pred[i], 1.0)) + '\n')
        w.close()
        print 'train mape:' + str(mape(y_tr, tr_pred, idx_tr, True))
