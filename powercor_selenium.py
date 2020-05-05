import os
import time
import glob
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

debug = True # debug true to print and screenshot as code runs
headless = True # toggle to false if you need to see the browser

log_count = 1
dir = os.path.dirname(os.path.abspath(__file__))
# get chromedriver from https://sites.google.com/a/chromium.org/chromedriver/downloads
chromedriver = os.path.join(dir, "chromedriver.exe") # TODO: check path for existence first - also don't assume windows

# debug logger
def logger(msg=""):
    global log_count
    global driver
    global dir
    global debug

    if debug:
        msg = "{}. {}".format(log_count, msg)
        print(msg)
        driver.save_screenshot(os.path.join(dir, "screenshot_{}.png".format(log_count)))
        log_count+=1

# lazy cleanup from previous runs
for filePath in (glob.glob('*CITIPOWER_DETAILED.csv') + glob.glob('screenshot_*.png')):
    try:
        os.remove(filePath)
    except:
        print("Error while deleting file : ", filePath)

# load dot env and get username and password
load_dotenv()
powercor = {
    'username': os.getenv("POWERCOR_USERNAME"),
    'password': os.getenv("POWERCOR_PASSWORD"),
    'login_url': 'https://customermeterdata.portal.powercor.com.au/customermeterdata/CADAccountPage',
    'usage_url': 'https://customermeterdata.portal.powercor.com.au/customermeterdata/CADRequestMeterData',
}

if not powercor['username']:
    raise ValueError("Specify POWERCOR_USERNAME in .env file")
if not powercor['password']:
    raise ValueError("Specify POWERCOR_PASSWORD in .env file")

# setup webdriver
options = webdriver.ChromeOptions()
if headless:
    options.add_argument('headless')
options.add_argument("log-level=3")
options.add_experimental_option("prefs", {
  "download.default_directory": dir,
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})

with webdriver.Chrome(executable_path=chromedriver, options=options) as driver:
    # load login page 
    driver.get('https://customermeterdata.portal.powercor.com.au/customermeterdata/CADAccountPage?startURL=%2Fcustomermeterdata%2FCADAccountPage')

    logger("Login page loaded")

    # fill in username/password and click login
    driver.find_element_by_css_selector('input[id$=\:username]').send_keys(powercor['username'])
    driver.find_element_by_css_selector('input[id$=\:password]').send_keys(powercor['password'])
    driver.find_element_by_css_selector("input[type='submit'][value='Login']").click()

    logger("Login attempted")

    # check for existence of "You are logged in as" to determine login success or not    
    try:
        WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, '//span[contains(text(),"You are logged in as ")]')))
    except:
        # get error
        try:
            error = driver.find_element_by_xpath("//div[@class='messageText']").text
        except:
            raise Exception("'You are logged in as' span wasn't found after clicking login and we didn't get an error message back from the page. Suggest disabling headless to troubleshoot") from None
        else:
            raise Exception("Error message from site: {}".format(error).replace("Error:\n","")) from None

    # TODO: add explicit check for multiple NMIs and add the ability to specify an NMI in .env to handle this case

    # click download data
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Download Data")]'))).click()

    logger("Logged in and clicked download data")

    # wait for meter data to load
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, "abc0")))

    logger("Meter data loaded")

    # wait for report type to be selectable, then select detailed report (csv)
    # this is still buggy and doesn't always select the field
    # probably need to wait until the option exists, not just the select itself
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "reportType")))
    Select(driver.find_element_by_id('reportType')).select_by_visible_text('Detailed Report (CSV)')

    # wait then click request meter data
    driver.implicitly_wait(1) # might help with above bug but now I'm not convinced
    driver.find_element_by_xpath("//input[@value='Request Meter Data']").click()

    logger("Clicked request meter data, now waiting for csv to download")

    # sleep until csv exists
    timeout_max = 30
    timeout = 0
    while not glob.glob('*CITIPOWER_DETAILED.csv'):
        if timeout_max == timeout:
            break
        time.sleep(1)
        timeout+=1

    logger("CSV should have been downloaded")

    driver.quit() # TODO: make sure this is still needed when enclosed in a with