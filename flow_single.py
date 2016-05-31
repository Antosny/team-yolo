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
allorder = ''

def load_map(path):
    '''load clustermap'''
    a = open(path).read().split('\n')[1:-1]
    for line in a:
        place, idx = line.split(',')
        place_map[place] = int(idx)

def load_test(path):
    '''load test date'''
    a = open(path).read().split('\n')[:-1]
    for line in a:
        testset.add(util.ts_idx(line))
    return testset

def is_test_data(ts):
    for i in range(0, 1):
        if int(ts) + i in testset:
            return True
    return False

def split_data(order, vali = True):
    if vali:
        order['test'] = order['tsidx'].apply(is_test_data)
        #split data into train & validation
        traindata = order[order['test'] == False]
        testdata = order[order['test'] == True]
        traindata.index = traindata[['start_district_hash', 'tsidx']]
        idx = pd.MultiIndex.from_tuples(traindata.index)
        traindata.index = idx
        testdata.index = testdata[['start_district_hash', 'tsidx']]
        idx = pd.MultiIndex.from_tuples(testdata.index)
        testdata.index = idx
        #if validation, return traindata and validationdata
        return traindata, testdata
    else:
        #if not validation, directly set index to place & timeslot and return
        traindata = order
        traindata.index = traindata[['start_district_hash', 'tsidx']]
        idx = pd.MultiIndex.from_tuples(traindata.index)
        traindata.index = idx
        return traindata

def ts_feature(ts):
    '''time slot features'''
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
    #is weekend
    feature.append(weekend)
    #week feature
    feature.append(dt.isoweekday())
    #hour feature
    feature.append(dt.hour)
    #minute feature
    feature.append(dt.minute)
    return feature

def transform(data, istrain = True):
    ''' transform data(pd.DataFrame) to train data fit for sklearn
    if istraindata, features are generated using allorder
    if istestdata, features are generated using data    
    return x, y, index, sample_weight
    '''
    x = []
    y = []
    idx = []
    weight = []
    datadict = data.to_dict('index')
    if istrain:
        for place, ts in datadict:
            if place not in place_map:
                continue
            #skip data in 2016-01-01 ~ 2016-01-03
            if int(ts) <= 576:
                continue
            #get label
            label = float(datadict[(place, ts)]['gap'])
            y.append(label)
            x.append(get_feature(place, ts, allorder))
            #index array inorder to match each train vector with place & timeslot
            idx.append([place, ts])
            if label == 0:
                weight.append(0.1)
            else:
                weight.append(1./label)
    else:
        for place in place_map:
            for ts in testset:
                label = -1
                if (place, ts) in datadict:
                    label = datadict[(place, ts)]['gap']
                y.append(label)
                x.append(get_feature(place, ts, datadict))
                idx.append([place, ts])

    return x, y, np.array(idx), weight



def get_feature(place, ts, datadict):
    '''
    given a (place, ts) pair, and datadict. Generate features of the pair
    return f, a feature array
    '''
    f = []
    #place index feature
    f.append(place_map[place])
    #time slot features
    f += ts_feature(ts)
    #previous gap
    for i in range(1, 2):
        if (place, ts - i) in datadict:
            f.append(datadict[(place, ts - i)]['gap'])
            f.append(datadict[(place, ts - i)]['call'])
            f.append(datadict[(place, ts - i)]['answer'])
            #answer rate of previous gap
            f.append((1. + datadict[(place, ts - i)]['answer']) / (1. + datadict[(place, ts - i)]['call']))
            #order per min(gap, call, answer)
            gapinfo = datadict[(place, ts - i)]['order_min'].split(':')
            #price per min(averagecall, averageanswer)
            priceinfo = datadict[(place, ts - i)]['price_min'].split(':')
            #for j in range(0, len(gapinfo)):
                #gap_min = gapinfo[j].split(',')
                #for g in gap_min:
                #    f.append(int(g))
                # for j in range(0, len(priceinfo)):
                #     price_min = priceinfo[j].split(',')
                #     for p in price_min:
                #         f.append(float(g))
        else:
            #if not match, add #n zeros
            for j in range(0, 4):
                f.append(0)
    return f


def mape(y_true, y_pred, idx, istrain = False):
    '''caculate mape for testdata'''
    lenplace = len(set(idx[:, 0]))
    if istrain:
        divider = lenplace * len(set(idx[:, 1])) * 1.
    else:
        divider = lenplace * len(testset) * 1.
    result_mape = 0.0
    calibration_mape = 0.0
    placemape = {}
    gapmean = {}
    for i in range(0, len(y_true)):
        place, ts = idx[i]
        if not istrain and int(ts) not in testset:
            continue
        if y_true[i] > 0:
            if place not in placemape:
                placemape[place] = 0.0
            result_mape += abs((y_true[i] - y_pred[i]) / (y_true[i] * 1.))
            cali_pred = y_pred[i]
            if y_true[i] not in gapmean:
                gapmean[y_true[i]] = []
            gapmean[y_true[i]].append(y_pred[i])
            if cali_pred > 5:
                cali_pred *= 1.2
            calibration_mape += abs((y_true[i] - cali_pred) / (y_true[i] * 1.))
            placemape[place] += abs((y_true[i] - y_pred[i]) / (y_true[i] * 1.))
    for gap in sorted(gapmean.keys()):
        print 'gap:' + str(gap) + ' count:' + str(len(gapmean[gap])) + ' average:' + str(sum(gapmean[gap]) / len(gapmean[gap]))
    for place in sorted(placemape.keys()):
        print place + ' mape:' + str(placemape[place] / (divider / lenplace))
    print 'calibration mape:' + str(calibration_mape / divider)
    return result_mape / divider
    


if __name__ == '__main__':
    '''    
    vali params:
    vadidationdates, trainorder, cluster_map

    test params:
    testdates, trainorder, testorder, cluster_map, output_file
    '''
    if len(sys.argv) < 2:
        print 'usage: python flow.py vali|test param'
        sys.exit(1)
    #init a gbrt model
    gbrt = GradientBoostingRegressor(loss='lad', max_depth=8, n_estimators=100)

    if sys.argv[1] == 'vali':
        valipath = sys.argv[2]
        orderpath = pd.read_csv(sys.argv[3])
        load_test(valipath)
        load_map(sys.argv[4])
        allorder = split_data(orderpath, False).to_dict('index')
        traindata, testdata = split_data(orderpath, True)
        x_tr, y_tr, idx_tr, weight_tr = transform(traindata)
        #write ytk-learn format data
        w = open('train.data', 'w')
        for i in range(0, len(weight_tr)):
           w.write(str(weight_tr[i]) + ':::' + str(y_tr[i]) + ':::' + '$'.join([str(x) for x in x_tr[i]]) + '\n')
        w.close()
        print '---------------'
        x_te, y_te, idx_te, weight_te = transform(testdata)
        #write ytk-learn format data
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
        traindata = split_data(pd.read_csv(orderpath), False)
        allorder = traindata.to_dict('index')
        testdata = split_data(pd.read_csv(testorderpath), False)
        x_tr, y_tr, idx_tr, weight_tr = transform(traindata)
        w = open('train.data.all', 'w')
        for i in range(0, len(weight_tr)):
           w.write(str(weight_tr[i]) + ':::' + str(y_tr[i]) + ':::' + '$'.join([str(x) for x in x_tr[i]]) + '\n')
        w.close()
        print '---------------'
        x_te, y_te, idx_te, weight_te = transform(testdata, False)
        print len(x_te)
        w = open('test.data.all', 'w')
        for i in range(0, len(y_te)):
           ts = int(idx_te[i][1])
           if ts not in testset:
               continue
           w.write(str(1) + ':::' + str(y_te[i]) + ':::' + '$'.join([str(x) for x in x_te[i]]) + '\n')
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
            #print place + ' ' + ts
            pred = y_pred[i]
            w.write(place + ',' + ts + ',' + str(max(pred, 1.0)) + '\n')
        w.close()
        print 'train mape:' + str(mape(y_tr, tr_pred, idx_tr, True))
        print 'test mape:' + str(mape(y_te, y_pred, idx_te, True))
