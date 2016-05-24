import numpy as np
import pandas as pd
import sys
import os
import util
from datetime import datetime
from sklearn.linear_model import *
from sklearn.ensemble import *

testset = set()
place_map = {}

def load_map(path):
    a = open(path).read().split('\n')[:-1]
    for line in a:
        place, idx = line.split('\t')
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
        if util.ts_idx(ts) + i in testset:
            return True
    return False

def split_data(order):
    order['test'] = order['ts'].apply(is_test_data)
    traindata = order[order['test'] == False]
    testdata = order[order['test'] == True]
    traindata.index = traindata[['start_district_hash', 'tsidx']]
    idx = pd.MultiIndex.from_tuples(traindata.index)
    traindata.index = idx
    testdata.index = testdata[['start_district_hash', 'tsidx']]
    idx = pd.MultiIndex.from_tuples(testdata.index)
    testdata.index = idx
    return traindata, testdata

def ts_feature(ts):
    ts = util.idx_ts(int(ts))
    tsinfo = ts.split('-')
    tshour = (int(tsinfo[-1]) - 1) / 6
    tsmin = 10 * ((int(tsinfo[-1]) - 1) % 6)
    tsstr = '-'.join(tsinfo[:-1]) + '-' + str(tshour) + '-' + str(tsmin)
    dt = datetime.strptime(tsstr, '%Y-%m-%d-%H-%M')
    feature = []
    feature.append(dt.isoweekday())
    feature.append(dt.hour)
    feature.append(dt.minute)
    return feature

def transform(data):
    x = []
    y = []
    idx = []
    weight = []
    datadict = data.to_dict('index')
    for place, ts in datadict:
        if place not in place_map:
            print place
            continue
        label = float(datadict[(place, ts)]['gap'])
        
        #if label == 0:
        #    continue
        y.append(label)
        #convert feature
        f = []
        f.append(place_map[place])
        f += ts_feature(ts)
        #previous gap
        for i in range(1, 2):
            if (place, ts - i) in datadict:
                f.append(datadict[(place, ts - i)]['gap'])
                f.append(datadict[(place, ts - i)]['call'])
                f.append(datadict[(place, ts - i)]['answer'])
            else:
                f.append(0)
                f.append(0)
                f.append(0)
        x.append(f)
        idx.append([place, ts])
        if label == 0:
            weight.append(0.1)
        else:
            weight.append(1./label)
    # for place in data.index.levels[0]:
    #     tsset = set(data.loc[place].index)
    #     print place
    #     for ts in tsset:
    #         y.append(data.loc[place, ts]['gap'])
    #         if ts - 1 in tsset:
    #             x.append(data.loc[place, ts - 1]['gap'])
    #         else:
    #             x.append(0)        
    return x, y, np.array(idx), weight

def mape(y_true, y_pred, idx, istrain = False):
    lenplace = len(set(idx[:, 0]))
    if istrain:
        divider = lenplace * len(set(idx[:, 1])) * 1.
    else:
        divider = lenplace * len(testset) * 1.
    result_mape = 0.0
    for i in range(0, len(y_true)):
        place, ts = idx[i]
        if not istrain and int(ts) not in testset:
            #print ts
            continue
        if y_true[i] > 0:
            result_mape += abs((y_true[i] - y_pred[i]) / (y_true[i] * 1.))
    return result_mape / divider
    

if __name__ == '__main__':
    testpath = sys.argv[1]
    orderpath = sys.argv[2]
    load_test(testpath)
    load_map(sys.argv[3])
    traindata, testdata = split_data(load_data(orderpath))
    x_tr, y_tr, idx_tr, weight_tr = transform(traindata)
    print '---------------'
    x_te, y_te, idx_te, weight_te = transform(testdata)
    print 'size of training:' + str(len(y_tr))
    print 'size of test:' + str(len(y_te))
    gbrt = GradientBoostingRegressor(loss='lad', max_depth=6)
    gbrt.fit(x_tr, y_tr, sample_weight = weight_tr)
    tr_pred = gbrt.predict(x_tr)
    y_pred = gbrt.predict(x_te)
    print 'train mape:' + str(mape(y_tr, tr_pred, idx_tr, True))
    print 'validation mape:' + str(mape(y_te, y_pred, idx_te))
