import os
import time
import glob
import csv
from statistics import median

dir = os.path.dirname(os.path.abspath(__file__))

csv_files = glob.glob('*CITIPOWER_DETAILED.csv')

if not csv_files:
    raise Exception("Missing csv")

# get latest csv
csv_file = max(csv_files, key=os.path.getctime)

# create header for csv
header = ["IntervalValue"+str(i) for i in range(-1, 48)]
header[0] = "RecordIndicator"
header[1] = "IntervalDate"

#num_lines = sum(1 for line in open('myfile.txt'))

with open(csv_file, "r") as f:
    # skip first 2 rows
    f.__next__()
    f.__next__()

    reader = csv.DictReader(f, header)

    rows = []
    for row in reader:
        # ignore records that aren't of type 300
        if row['RecordIndicator'] == '300':
            rows.append(row)

# only keep last 120 rows (days)
# TODO: test on data with less than 120 days
rows = rows[-120:]

# we want IntervalValue10 to 16 which represents 3am-6am
dead_of_night = range(10,16)

historical_data = []
last_nights_data = []

# create list of values from dead of night
for row in rows:
    for i in dead_of_night:
        # TODO: might ignore zeroes
        historical_data.append(float(row["IntervalValue{}".format(i)]))

# get last nights data
for i in dead_of_night:
    last_nights_data.append(float(rows[-1]["IntervalValue{}".format(i)]))

# get historical and last nights median
historical_median = median(historical_data)
historical_median_plus10 = historical_median * 1.1
historical_median_plus20 = historical_median * 1.2
last_nights_median = median(last_nights_data)

# check every day to see which ones were above/below median
print("Date    \tMedian\t+10%\t+20%")
for row in rows:
    nightly_data = []
    for i in dead_of_night:
        nightly_data.append(float(row["IntervalValue{}".format(i)]))
    
    nightly_median = median(nightly_data)

    if nightly_median > historical_median_plus10 or nightly_median > historical_median_plus20:
        print("{}\t{}\t{}\t{}".format(row['IntervalDate'], round(nightly_median,4), nightly_median > historical_median_plus10, nightly_median > historical_median_plus20))

print()
print("Historical median: {}".format(historical_median))
print("Historical median +10%: {}".format(historical_median_plus10))
print("Historical median +20%: {}".format(historical_median_plus20))
print("Last nights median: {}".format(last_nights_median))

if last_nights_median > historical_median_plus10:
    "Last night you used more power than the historical media + 10% ({})".format(historical_median_plus10)

if last_nights_median > historical_median_plus20:
    "Last night you used more power than the historical media + 20% ({})".format(historical_median_plus20)