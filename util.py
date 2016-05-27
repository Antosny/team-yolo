import os
import sys
import pandas as pd
import numpy as np
def convert_ts(timestamp):
    day, t = timestamp.split(' ')
    h, m, s = t.split(':')
    result = day + '-' + str(int(h) * 6 + int(m) / 10 + 1)
    return result

def ts_idx(ts):
    tinfo = ts.split('-')
    return int(tinfo[2]) * 144 + int(tinfo[3])

def idx_ts(idx):
    slot = idx % 144
    if slot == 0:
        slot = 144
    day = (idx - 1) / 144
    if day < 10:
        day = '0' + str(day)
    else:
        day = str(day)
    return '2016-01-' + day + '-' + str(slot) 

def answer(x):
    if x is np.nan:
        return 0
    return 1

def order_to_ts(fromfile, tofile):
    a = pd.read_csv(fromfile)
    a['ts'] = a['time'].apply(convert_ts)
    a = a.drop('time', 1)
    a['call'] = a['ts'].apply(lambda x:1)
    a['answer'] = a['driver_id'].apply(answer)
    a = a.drop('passenger_id', 1)
    a = a.drop('driver_id', 1)
    agroup = a.groupby(['start_district_hash', 'ts'])
    suma = agroup.sum()
    suma['gap'] = suma['call'] - suma['answer']
    suma = suma.drop('price', 1)
    #suma['tsidx'] = suma['ts'].apply(ts_idx)
    suma.to_csv(tofile)
    suma = pd.read_csv(tofile)
    suma['tsidx'] = suma['ts'].apply(ts_idx)
    suma.to_csv(tofile, index=False)
    return suma

def add_header(dirpath, topath):
    order = ['order_id', 'driver_id', 'passenger_id', 'start_district_hash', 'dest_district_hash', 'price', 'time']
    poi = ['district_hash', 'poi_class']
    cluster = ['district_hash', 'district_id']
    traffic = ['district_hash', 'tj_level', 'tj_time']
    weather = ['time', 'weather', 'temp', 'pm2.5']
    os.mkdir(topath)
    dirs = os.listdir(dirpath)
    for d in dirs:
        if not os.path.isdir(dirpath + '/' + d):
            continue
        print d
        os.mkdir(topath + '/' + d)
        flist = os.listdir(dirpath + '/' + d)
        wall = open(topath + '/' + d + '/' + d + '_all', 'w')
        if d.find('order') != -1:
            wall.write(','.join(order) + '\n')
        if d.find('traffic') != -1:
            wall.write(','.join(traffic) + '\n')
        if d.find('weather') != -1:
            wall.write(','.join(weather) + '\n')
        
        for f in flist:
            print f
            a = open(dirpath + '/' + d + '/' + f).read().split('\n')[:-1]
            w = open(topath + '/' + d + '/' + f, 'w')
            if d.find('order') != -1:
                w.write(','.join(order) + '\n')
                for line in a:
                    w.write(','.join(line.split('\t')) + '\n')
                    wall.write(','.join(line.split('\t')) + '\n')
            if d.find('poi') != -1:
                w.write(','.join(poi) + '\n')
                for line in a:
                    hinfo = line.split('\t')
                    w.write(hinfo[0] + ',' + '\t'.join(hinfo[1:]) + '\n')
            if d.find('traffic') != -1:
                w.write(','.join(traffic) + '\n')
                for line in a:
                    tinfo = line.split('\t')
                    w.write(tinfo[0] + ',' + '\t'.join(tinfo[1:-1]) + ',' + tinfo[-1] + '\n')
                    wall.write(tinfo[0] + ',' + '\t'.join(tinfo[1:-1]) + ',' + tinfo[-1] + '\n')
            if d.find('cluster') != -1:
                w.write(','.join(cluster) + '\n')
                for line in a:
                    w.write(','.join(line.split('\t')) + '\n')
            if d.find('weather') != -1:
                w.write(','.join(weather) + '\n')
                for line in a:
                    w.write(','.join(line.split('\t')) + '\n')
                    wall.write(','.join(line.split('\t')) + '\n')
            w.close()



if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'usage: python util.py header|order frompath topath'
    if sys.argv[1] == 'header':
        add_header(sys.argv[2], sys.argv[3])
    if sys.argv[1] == 'order':
        order_to_ts(sys.argv[2], sys.argv[3])
    else:
        print 'usage: python util.py header|order frompath topath'
