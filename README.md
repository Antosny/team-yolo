1. extract train & test data
2. add headers to train & test data. python util.py header training_data/ topath/
3. convert 'orderdata' to 'orderdatagroup by timeslot'. python util.py order topath/order_data/order_data_all order_group
4. run script to train & test in validation set. python flow_single.py vali validation.txt order_group topath/cluster_map/cluster_map 
