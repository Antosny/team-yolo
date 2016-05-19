def convert_ts(timestamp):
    day, t = timestamp.split(' ')
    h, m, s = t.split(':')
    result = day + '-' + str(int(h) * 6 + int(m) / 10 + 1)
    return result


if __name__ == '__main__':
    print convert_ts('2016-01-07 23:45:42')
