import os
import time
import glob
import csv
from statistics import median, stdev, mean

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
# TODO: rethink this, because electricity usage available each day only shows the previous data up until midnight
for row in rows:
    for i in dead_of_night:
        # TODO: might ignore zeroes
        historical_data.append(float(row["IntervalValue{}".format(i)]))

# get last nights data
for i in dead_of_night:
    last_nights_data.append(float(rows[-1]["IntervalValue{}".format(i)]))

# get historical and last nights median
historical_median = median(historical_data)
historical_mean = round(mean(historical_data),4)
historical_stdev = round(stdev(historical_data),4)
historical_medstdev = historical_median + historical_stdev
historical_meanstdev = historical_mean + historical_stdev
last_nights_median = median(last_nights_data)

# check every day to see which ones were above/below median
print("Date    \tMedian\t+Med+stdev\tMean+stdev")
for row in rows:
    nightly_data = []
    for i in dead_of_night:
        nightly_data.append(float(row["IntervalValue{}".format(i)]))
    
    nightly_median = median(nightly_data)

    if nightly_median > historical_medstdev or nightly_median > historical_meanstdev:
        print("{}\t{}\t{}\t\t{}".format(row['IntervalDate'], round(nightly_median,4), nightly_median > historical_medstdev, nightly_median > historical_meanstdev))

print()
print("Historical median: {}".format(historical_median))
print("Historical mean: {}".format(historical_mean))
print("Historical stdev: {}".format(historical_stdev))
print("Historical median+stdev: {}".format(historical_medstdev))
print("Historical mean+stdev: {}".format(historical_meanstdev))
print("Last nights median: {}".format(last_nights_median))

if last_nights_median > historical_meanstdev:
    "Last night you used more power than the historical mean + stdev ({})".format(historical_meanstdev)
