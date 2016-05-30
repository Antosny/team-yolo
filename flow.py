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
allorder = ''
toorder = ''
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

def load_to_data(todata):
    tod = pd.read_csv(todata)
    tod.index = tod[['dest_district_hash', 'tsidx']]
    return tod.to_dict('index')

def is_test_data(ts):
    for i in range(0, 1):
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
    week = 0
    if dt.isoweekday() < 6:
        week = 1
    feature.append(week)
    feature.append(dt.isoweekday())
    feature.append(dt.hour)
    feature.append(dt.minute)
    return feature

def transform_per_place(data, istrain = True):
    x = {}
    y = {}
    idx = {}
    weight = {}
    datadict = data.to_dict('index')
    if istrain:
        for place, ts in datadict:
            if place not in place_map:
                continue
            #if int(ts) <= 576:
            #    continue
            if place not in x:
                x[place] = []
                y[place] = []
                idx[place] = []
                weight[place] = []
            label = float(datadict[(place, ts)]['gap'])
            y[place].append(label)
            x[place].append(get_feature(place, ts, allorder))
            idx[place].append([place, ts])
            if label == 0:
                weight[place].append(0.001)
            else:
                weight[place].append(1./label)
    else:
        for place in place_map:
            x[place] = []
            y[place] = []
            idx[place] = []
            for ts in testset:
                y[place].append(-1)
                x[place].append(get_feature(place, ts, datadict))
                idx[place].append([place, ts])

    return x, y, idx, weight


def get_feature(place, ts, datadict):
    f = []
    f.append(place_map[place])
    f += ts_feature(ts)
    #previous gap
    for i in range(1, 2):
        if (place, ts - i) in datadict:
            f.append(datadict[(place, ts - i)]['gap'])
            f.append(datadict[(place, ts - i)]['call'])
            f.append(datadict[(place, ts - i)]['answer'])
            gapinfo = datadict[(place, ts - i)]['order_min'].split(':')
            priceinfo = datadict[(place, ts - i)]['price_min'].split(':')
            for j in range(0, len(gapinfo)):
                gap_min = gapinfo[j].split(',')
                for g in gap_min:
                    f.append(int(g))
        else:
            for j in range(0, 33):
                f.append(0)

    tosum = 0
    for i in range(1, 2):
        if (place, ts - i) in toorder:
            tosum += toorder[(place, ts - i)]['answer']
            f.append(toorder[(place, ts - i)]['answer'])
        else:
            for j in range(0, 1):
                f.append(0)
    #f.append(tosum)

    return f



def mape_per_place(y_true, y_pred, idx, istrain = False):
    lenplace = len(y_pred)
    if istrain:
        dateidx = max([len(x) for x in y_true.values()])
        divider = lenplace * dateidx * 1.
    else:
        divider = lenplace * len(testset) * 1.
    result_mape = 0.0
    cali_mape = 0.0
    print '----mape----'
    placem = {}
    gapmean = {}
    for place in y_pred:
        #print place
        pmap = 0.0
        for i in range(0, len(y_true[place])):
            #print i
            p, ts = idx[place][i]
            if not istrain and int(ts) not in testset:
                continue
            if y_true[place][i] > 0:
                if y_true[place][i] not in gapmean:
                    gapmean[y_true[place][i]] = []
                gapmean[y_true[place][i]].append(y_pred[place][i])
                calipred = y_pred[place][i]
                if calipred > 10:
                    calipred *= 1.1
                result_mape += abs((y_true[place][i] - y_pred[place][i]) / (y_true[place][i] * 1.))
                pmap += abs((y_true[place][i] - y_pred[place][i]) / (y_true[place][i] * 1.))
                cali_mape += abs((y_true[place][i] - calipred) / (y_true[place][i] * 1.))
        placem[place] = pmap / (divider / lenplace)
        
    for gap in sorted(gapmean.keys()):
        print 'gap:' + str(gap) + ' count:' + str(len(gapmean[gap])) + ' average:' + str(sum(gapmean[gap]) / len(gapmean[gap]))

    for place in sorted(placem.keys()):
        print place + ' mape:' + str(placem[place])
    print 'calibration mape:' + str(cali_mape / divider)
    return result_mape / divider

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'usage: python flow.py vali|test params'
        sys.exit(1)
    gbrt = GradientBoostingRegressor(loss='lad', max_depth=8)
    if sys.argv[1] == 'vali':
        valipath = sys.argv[2]
        orderpath = load_data(sys.argv[3])
        load_test(valipath)
        load_map(sys.argv[4])
        toorder = load_to_data(sys.argv[5])
        allorder = split_data(orderpath, False)
        allorder = allorder.to_dict('index')
        traindata, testdata = split_data(orderpath, True)
        x_tr, y_tr, idx_tr, weight_tr = transform_per_place(traindata)
        #print idx_tr.keys()
        #w = open('train.data', 'w')
        #for i in range(0, len(weight_tr)):
        #    w.write(str(weight_tr[i]) + ':::' + str(y_tr[i]) + ':::' + '$'.join([str(x) for x in x_tr[i]]) + '\n')
        #w.close()
        print '---------------'
        x_te, y_te, idx_te, weight_te = transform_per_place(testdata)
        #print idx_te.keys()
        #w = open('test.data', 'w')
        #for i in range(0, len(weight_te)):
        #    ts = int(idx_te[i][1])
        #    if ts not in testset:
        #        continue
        #    w.write(str(weight_te[i]) + ':::' + str(y_te[i]) + ':::' + '$'.join([str(x) for x in x_te[i]]) + '\n')
        #w.close()
        print 'size of training:' + str(len(y_tr))
        print 'size of test:' + str(len(y_te))
        model = {}
        tr_pred = {}
        y_pred = {}
        for place in x_tr:
            #if place != '62afaf3288e236b389af9cfdc5206415':
            #    continue
            print place
            gbrt = GradientBoostingRegressor(loss='lad', max_depth=6, n_estimators=200)
            gbrt.fit(x_tr[place], y_tr[place], sample_weight = weight_tr[place])
            model[place] = gbrt
            tr_pred[place] = gbrt.predict(x_tr[place])
            y_pred[place] = gbrt.predict(x_te[place])
        #gbrt.fit(x_tr, y_tr, sample_weight = weight_tr)
        #tr_pred = gbrt.predict(x_tr)
        #y_pred = gbrt.predict(x_te)
        print 'train mape:' + str(mape_per_place(y_tr, tr_pred, idx_tr, True))
        print 'validation mape:' + str(mape_per_place(y_te, y_pred, idx_te))
    if sys.argv[1] == 'test':
        testpath = sys.argv[2]
        orderpath = sys.argv[3]
        testorderpath = sys.argv[4]
        load_test(testpath)
        load_map(sys.argv[5])
        traindata = split_data(load_data(orderpath), False)
        testdata = split_data(load_data(testorderpath), False)
        x_tr, y_tr, idx_tr, weight_tr = transform_per_place(traindata)
        print '---------------'
        x_te, y_te, idx_te, weight_te = transform_per_place(testdata, False)
        print 'size of training:' + str(len(y_tr))
        print 'size of test:' + str(len(y_te))
        model = {}
        tr_pred = {}
        y_pred = {}
        for place in x_tr:
            print place
            gbrt = GradientBoostingRegressor(loss='lad', max_depth=4)
            gbrt.fit(x_tr[place], y_tr[place], sample_weight = weight_tr[place])
            model[place] = gbrt
            tr_pred[place] = gbrt.predict(x_tr[place])
            y_pred[place] = gbrt.predict(x_te[place])

        w = open(sys.argv[6], 'w')
        for place in y_pred:
            for i in range(0, len(y_pred[place])):
                ts = str(util.idx_ts(int(idx_te[place][i][1])))
                print place + ' ' + ts
                pre = y_pred[place][i]
                if pre > 10:
                    pre *= 1.3
                w.write(place + ',' + ts + ',' + str(max(pre, 1.0)) + '\n')
        w.close()
        print 'train mape:' + str(mape_per_place(y_tr, tr_pred, idx_tr, True))
