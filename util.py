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

def comma_join(l):
    return ','.join([str(i) for i in l])

def order_min(l):
    info = l.split('#@#')
    answer = np.zeros(10)
    call = np.zeros(10)
    timelist = info[0].split(',')
    orderlist = info[2].split(',')
    for i in range(0, len(timelist)):
        idx = int(timelist[i].split(':')[1][-1])
        call[idx] += 1
        if orderlist[i] != 'nan':
            answer[idx] += 1
    gap = call - answer
    result = ''
    for i in range(0, len(answer)):
        result += str(int(call[i])) + ',' + str(int(answer[i])) + ',' + str(int(gap[i])) + ':'
    return result[:-1]

def price_min(l):
    info = l.split('#@#')
    answer = np.zeros(10)
    call = np.zeros(10)
    answer_cnt = np.zeros(10)
    call_cnt = np.zeros(10)
    timelist = info[0].split(',')
    pricelist = info[1].split(',')
    orderlist = info[2].split(',')
    for i in range(0, len(timelist)):
        idx = int(timelist[i].split(':')[1][-1])
        call[idx] += float(pricelist[i])
        call_cnt[idx] += 1
        if orderlist[i] != 'nan':
            answer[idx] += float(pricelist[i])
            answer_cnt[idx] += 1
    answer_cnt[answer_cnt == 0] = 1
    call_cnt[call_cnt == 0] = 1
    answer = answer / answer_cnt
    call = call / call_cnt
    
    result = ''
    for i in range(0, len(answer)):
        result += str(call[i]) + ',' + str(answer[i]) + ':'
    return result[:-1]


def order_to_ts_min(fromfile, tofile):
    a = pd.read_csv(fromfile)
    a['tsidx'] = a['time'].apply(convert_ts)
    a['tsidx'] = a['tsidx'].apply(ts_idx)
    agroup = a.groupby(['start_district_hash', 'tsidx'])
    agroup = agroup.agg({'time':comma_join, 'price':comma_join, 'driver_id':comma_join})
    agroup['info'] = agroup['time'] + '#@#' + agroup['price'] + '#@#' + agroup['driver_id']
    agroup = agroup.drop('time', 1)
    agroup = agroup.drop('price', 1)
    agroup = agroup.drop('driver_id', 1)
    agroup['answer'] = agroup['info'].apply(lambda x:len([i for i in x.split('#@#')[2].split(',') if i != 'nan']))
    agroup['call'] = agroup['info'].apply(lambda x:len([i for i in x.split('#@#')[2].split(',')]))
    agroup['gap'] = agroup['call'] - agroup['answer']
    agroup['order_min'] = agroup['info'].apply(order_min)
    agroup['price_min'] = agroup['info'].apply(price_min)
    agroup.to_csv(tofile, index=True)
    return agroup

def order_to_ts_min_toplace(fromfile, tofile):
    a = pd.read_csv(fromfile)
    a['tsidx'] = a['time'].apply(convert_ts)
    a['tsidx'] = a['tsidx'].apply(ts_idx)
    agroup = a.groupby(['dest_district_hash', 'tsidx'])
    agroup = agroup.agg({'time':comma_join, 'price':comma_join, 'driver_id':comma_join})
    agroup['info'] = agroup['time'] + '#@#' + agroup['price'] + '#@#' + agroup['driver_id']
    agroup = agroup.drop('time', 1)
    agroup = agroup.drop('price', 1)
    agroup = agroup.drop('driver_id', 1)
    agroup['answer'] = agroup['info'].apply(lambda x:len([i for i in x.split('#@#')[2].split(',') if i != 'nan']))
    agroup['call'] = agroup['info'].apply(lambda x:len([i for i in x.split('#@#')[2].split(',')]))
    agroup['gap'] = agroup['call'] - agroup['answer']
    agroup['order_min'] = agroup['info'].apply(order_min)
    agroup['price_min'] = agroup['info'].apply(price_min)
    agroup.to_csv(tofile, index=True)
    return agroup




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
    if sys.argv[1] == 'ordermin':
        order_to_ts_min(sys.argv[2], sys.argv[3])
    if sys.argv[1] == 'orderminto':
        order_to_ts_min_toplace(sys.argv[2], sys.argv[3])
