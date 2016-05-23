import numpy as np
import pandas as pd
import sys
import os
import util
from sklearn.linear_model import *

testset = set()

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

def split_data(order, test):
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

def transform(data):
    x = []
    y = []
    datadict = data.to_dict('index')
    for place, ts in datadict:
        y.append(datadict[(place, ts)]['gap'])
        f = []
        f.append(1.0)
        if (place, ts - 1) in datadict:
            f.append(datadict[(place, ts - 1)]['gap'])
        else:
            f.append(0)
        x.append(f)
    datadict = {}
    # for place in data.index.levels[0]:
    #     tsset = set(data.loc[place].index)
    #     print place
    #     for ts in tsset:
    #         y.append(data.loc[place, ts]['gap'])
    #         if ts - 1 in tsset:
    #             x.append(data.loc[place, ts - 1]['gap'])
    #         else:
    #             x.append(0)        
    return x, y


if __name__ == '__main__':
    testpath = sys.argv[1]
    orderpath = sys.argv[2]
    load_test(testpath)
    traindata, testdata = split_data(load_data(orderpath), testset)
    x_tr, y_tr = transform(traindata)
    lr = LinearRegression()
    lr.fit(x_tr, np.array([y_tr]).T)
    print lr.coef_
    print lr.intercept_
