from collections import Counter, defaultdict
import re
import time
from geoip import geolite2


file_name = 'access.log.txt'


def get_data(name):
    log_file = open(name, 'r')

    parts = [
        r'(?P<host>\S+)',                   # host %h
        r'\S+',                             # indent %l (unused)
        r'(?P<user>\S+)',                   # user %u
        r'\[(?P<time>.+)\]',                # time %t
        r'"(?P<request>.*)"',               # request "%r"
        r'(?P<status>[0-9]+)',              # status %>s
        r'(?P<size>\S+)',                   # size %b (careful, can be '-')
        r'"(?P<referrer>.*)"',              # referrer "%{Referer}i"
        r'"\S+',                            # mozilla
        r'\((?P<OS>.*?)\)',                 # OS
        r'(?P<agent>.*)"',                  # user agent "%{User-agent}i"
    ]

    pattern = re.compile(r'\s+'.join(parts)+r'\s*\Z')
    log_data = []
    anomalies = []
    for line in log_file:
        m = pattern.match(line)
        if m:

            log_data.append(m.groupdict())
        else:
            anomalies.append(line.rstrip())

    return log_data, anomalies


def unique(log_data, anomalies):
    set_of_hosts = set()
    unique_data = []
    unique_bad = []

    for line in log_data:
        if line['host'] not in set_of_hosts:
            unique_data.append(line)
            set_of_hosts.add(line['host'])

    for line in anomalies:
        if line['host'] not in set_of_hosts:
            unique_bad.append(line)
            set_of_hosts.add(line['host'])

    return unique_data, unique_bad, set_of_hosts


def count_all(log_data):
    counter = defaultdict(Counter)

    for line in log_data:
        for key, value in line.items():
            counter[key].update([value])

    return counter


def get_country(log_data):
    countries = Counter()

    for host, count in log_data['host'].items():
        if host != '::1':
            a = geolite2.lookup(host)
            if a is not None:
                countries[a.country] += count

    return countries


def get_hour(log_data):
    hours = Counter()

    for time_, count in log_data['time'].items():
        hours[time_[12:14]] += count

    return hours


def handle_anomalies(anomalies):
    parts = [
        r'(?P<host>\S+)',  # host %h
        r'\S+',  # indent %l (unused)
        r'(?P<user>\S+)',  # user %u
        r'\[(?P<time>.+)\]',  # time %t
        r'"(?P<request>.*)"',  # request "%r"
        r'(?P<status>[0-9]+)',  # status %>s
        r'(?P<size>\S+)',  # size %b (careful, can be '-')
        r'"(?P<referrer>.*)"',  # referrer "%{Referer}i"
        r'"(?P<agent>.*)"',  # user agent "%{User-agent}i"
    ]
    pattern = re.compile(r'\s+'.join(parts) + r'\s*\Z')

    result = []
    for line in anomalies:
        m = pattern.match(line)
        if m:
            result.append(m.groupdict())

    return result


def main():
    log_data, anomalies = get_data(file_name)
    handled_anomalies = handle_anomalies(anomalies)

    unique_host, bad_requests, count_unique = unique(log_data, handled_anomalies)

    print("Number of unique ip: ", len(count_unique), "\n")
    print("Unique IP", count_unique, "\n")
    print("Bad requests: ", bad_requests, "\n")

    print("Count")
    counter = count_all(unique_host)
    counter_country = get_country(counter)
    counter_hours = get_hour(counter)
    print(counter_hours)
    print(counter['agent'])
    print(counter['OS'])
    print(counter_country, "\n")


start_time = time.clock()
main()
print(time.clock() - start_time, "seconds")