"""
File format
hour_index, value
"""


import datetime
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as ss


indexes = ['users', 'sessions', 'views']


def get_date(hour):
    year = 2018
    if hour < 744:
        day = hour // 24 + 1
        month = 1
    elif hour < 1416:
        day = (hour - 744) // 24 + 1
        month = 2
    elif hour < 2160:
        day = (hour - 1416) // 24 + 1
        month = 3
    else:
        day = (hour - 2160) // 24 + 1
        month = 4
    hour = hour % 24

    return datetime.datetime(year, month, day, hour)


def to_int(string):
    return int(string.replace("\xa0", ""))


def process_csv(file_name):
    dataset = pd.read_csv(file_name + ".csv", ",")
    dataset['hour_index'] = dataset['hour_index'].apply(lambda x: get_date(x))
    dataset.rename(columns={'hour_index': 'date'}, inplace=True)
    dataset.set_index('date', inplace=True)

    return dataset


def get_actual_data():
    dataframes = []
    for file in indexes:
        dataframes.append(process_csv(file))
    actual_data = pd.concat(dataframes, axis=1, join='inner')
    actual_data['views'] = actual_data['views'].apply(lambda x: to_int(x))

    return actual_data


def regression_analysis(actual_data, x, y):
    slope, intercept, rvalue, pvalue, stderr = ss.linregress(actual_data[x], actual_data[y])
    print("Linear equation for {} (x) and {} (y)".format(x, y))
    print("y = {}x + {}".format(slope, intercept))
    print("stderr: ", stderr)
    print("correlation coefficient: ", rvalue)
    estimated_value = actual_data[x]*slope + intercept
    measurement_err = actual_data.size*stderr
    right_bound = estimated_value + measurement_err
    left_bound = estimated_value - measurement_err
    out_left_bound = actual_data[y] < left_bound
    out_right_bound = actual_data[y] > right_bound
    anomalies_flag = out_right_bound | out_left_bound
    print("Was found {} anomalies".format(anomalies_flag.sum()))
    print("\n")
    anomalies = actual_data[anomalies_flag][y]
    plt.title("Anomalies for {}".format(y))
    plt.plot(anomalies, 'ro', markersize=3, label='Anomalies')
    plt.plot(actual_data[y], label='Actual data')
    plt.legend(loc='upper left')
    plt.show()

    return anomalies


def main():
    actual_data = get_actual_data()
    newlist = []
    for a,b in zip(actual_data['users'], actual_data['sessions']):
        newlist.append([a, b])

    regression_analysis(actual_data, 'users', 'sessions')
    regression_analysis(actual_data, 'users', 'views')


main()
