# coding: utf-8
import pandas as pd
import numpy as np
import os
order = pd.read_csv('../train_data/order_data/order_data_2016-01-12')
order['ts'] = order['time'].apply(util.convert_ts)
order = order.drop('time', 1)
order['call'] = order['passenger_id'].apply(lambda x:1)
def answer(f):
    if f is np.nan:
        return 0
    return 1
order['answer'] = order['driver_id'].apply(answer)
order = order.drop('driver_id', 1)
order = order.drop('passenger_id', 1)
ordergroup = order.groupby(['start_district_hash', 'ts'])
dd = ordergroup.sum()
dd['gap'] = dd['call'] - dd['answer']
poi = pd.read_csv('../train_data/poi_data/poi_data')
poi.index = poi['district_hash']
dd.reset_index(level=1).join(poi)
dd.reset_index(level=1).join(poi)
ddd = dd.reset_index(level=1).join(poi)
ddd.index = ddd['ts']
weather = pd.read_csv('../train_data/weather_data/weather_data_2016-01-12')
weather['ts'] = weather['time'].apply(util.convert_ts)
weather = weather.drop('time', 1)
ddd.join(weather)
weather = weather.drop_duplicates(subset='ts', take_last=True)
ddd = pd.merge(ddd, weather, left_index='ts', right_index='ts', how='outer')
traffic = pd.read_csv('../train_data/traffic_data/traffic_data_2016-01-12')
traffic['ts'] = traffic['tj_time'].apply(util.convert_ts)
traffic.index = traffic[['district_hash', 'ts']]
traffic.index
traffic.index.drop_duplicates()
ddd.index = ddd[['district_hash', 'ts_x']]
traffic = traffic.drop('district_hash', 1)
ddd.join(traffic)
ddd = ddd.drop('ts_y', 1)
