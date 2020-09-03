# electricity-usage

The general idea I had when starting this code was to figure out based on historical usage if I had left the heater or aircon on overnight.

My thermostat screen is behind a wall hanging and as it's a city apartment building, the central heating/cooling is a proprietary system and quiet and subtle enough that it's not obvious that it's on. This has resulted in me turning it on and not realising until several days later I hadn't turned it off.

The code downloads your power usage from the powercor/citipower portal, then figures out the historical median usage from 3am-6am, comparing it to the previous nights usage, looking for a telltale rise.

I schedule this code to run each morning to alert me to check my aircon/heater.

Giant caveat: The problem is that historical data is only made available for the previous day up to midnight, so this code will actually tell me 24h later. Not as useful as I had hoped, but still good for those times that I leave it on for a few days without realising.

_NB. Only tested on Windows so far_

## powercor_selenium.py

Download `chromedriver.exe` from https://sites.google.com/a/chromium.org/chromedriver/downloads and put it on `%path%`

Rename `sample.env` to `.env` and populate `POWERCOR_` values

- Toggle `debug` to false if you don't want screenshots and basic logging
- Toggle `headless` to false to enable the browser to be visible while running

Script cleans up after itself at the start of a run, removing csv and png

Success should end up with a csv named `*_CITIPOWER_DETAILED.csv` in the dir

## powercor_analysis.py

Using csv downloaded using `powercor_selenium.py`, figures out the historical (for last 120 days) median, mean, stdev of your usage from 3am-6am.

It then checks every nights median against the historical median+stdev and mean+stdev (still deciding which to rely on)

Also outputs previous nights median

```
Date            Median  Med+stdev       Mean+stdev
20200608        0.174   True            True
20200618        0.1365  True            True
20200713        0.1325  True            False
20200727        0.1335  True            True
20200729        0.1355  True            True
20200730        0.1325  True            False
20200731        0.142   True            True
20200801        0.133   True            False
20200802        0.135   True            True
20200814        0.134   True            True
20200824        0.171   True            True

Historical median: 0.117
Historical mean: 0.1184
Historical stdev: 0.0146
Historical median+stdev: 0.1316
Historical mean+stdev: 0.133
Last nights median: 0.1145
```
