# coding: utf-8
import pandas as pd
import numpy as np
import util

tr_order = pd.read_csv('order_data/order.all')
tr_order['ts'] = util.convert_ts[tr_order['time']]
