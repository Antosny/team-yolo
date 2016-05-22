import os
import sys
def convert_ts(timestamp):
    day, t = timestamp.split(' ')
    h, m, s = t.split(':')
    result = day + '-' + str(int(h) * 6 + int(m) / 10 + 1)
    return result


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
        for f in flist:
            print f
            a = open(dirpath + '/' + d + '/' + f).read().split('\n')[:-1]
            w = open(topath + '/' + d + '/' + f, 'w')
            if d.find('order') != -1:
                w.write(','.join(order) + '\n')
                for line in a:
                    w.write(','.join(line.split('\t')) + '\n')
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
            if d.find('cluster') != -1:
                w.write(','.join(cluster) + '\n')
                for line in a:
                    w.write(','.join(line.split('\t')) + '\n')
            if d.find('weather') != -1:
                w.write(','.join(weather) + '\n')
                for line in a:
                    w.write(','.join(line.split('\t')) + '\n')
            w.close()



if __name__ == '__main__':
    print convert_ts('2016-01-07 23:45:42')
    add_header(sys.argv[1], sys.argv[2])
