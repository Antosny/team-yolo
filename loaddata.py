import sys
import pandas as pd
import util
import numpy as np

def answer(x):
    if x is np.nan:
        return 0
    return 1

def loadorder(f, vali):
    order = pd.read_csv(f)
    v = set()
    a = open(vali).read().split('\n')[:-1]
    for line in a:
        v.add(line)
    order['ts'] = order['time'].apply(util.convert_ts)
    order['call'] = order['passenger_id'].apply(lambda x:1)
    order['answer'] = order['driver_id'].apply(answer)
    order = order.drop('time', 1)
    order = order.drop('passenger_id', 1)
    order = order.drop('driver_id', 1)
    

if __name__ == '__main__':
    loadorder(sys.argv[1], sys.argv[2])
    
