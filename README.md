# electricity-usage

Only tested on Windows so far

## powercor_selenium.py

Download `chromedriver.exe` from https://sites.google.com/a/chromium.org/chromedriver/downloads and put it on `%path%`

Rename `sample.env` to `.env` and populate `POWERCOR_` values

- Toggle `debug` to false if you don't want screenshots and basic logging
- Toggle `headless` to false to enable the browser to be visible while running

Script cleans up after itself at the start of a run, removing csv and png

Success should end up with a csv file in the dir
