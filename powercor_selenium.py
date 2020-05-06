import os
import time
import glob
import re
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from dateutil.relativedelta  import relativedelta

debug = True # debug true to print and screenshot as code runs
headless = True # toggle to false if you need to see the browser

log_count = 1
dir = os.path.dirname(os.path.abspath(__file__))

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
    'nmi': os.getenv("POWERCOR_NMI"), # optional and ignored if user only has one nmi in their portal
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
if debug:
    options.add_argument('window-size=800,1024')
options.add_argument("log-level=3")
options.add_experimental_option("prefs", {
  "download.default_directory": dir,
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})

# get chromedriver from https://sites.google.com/a/chromium.org/chromedriver/downloads
with webdriver.Chrome(options=options) as driver:
    # load login page 
    driver.get('https://customermeterdata.portal.powercor.com.au/customermeterdata/CADAccountPage?startURL=%2Fcustomermeterdata%2FCADAccountPage')

    logger("Login page loaded")

    # fill in username/password and click login
    driver.find_element_by_css_selector('input[name$=\:username]').send_keys(powercor['username'])
    driver.find_element_by_css_selector('input[name$=\:password]').send_keys(powercor['password'])
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

    # wait until NMIs are loaded
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//span[contains(text(),"Showing ")]')))

    # count how many checkboxes there are - more than 2 means there are multiple NMIs in the portal and we need to know which to use
    checkboxes_count = len(driver.find_elements_by_css_selector("input[type='checkbox']"))
    if checkboxes_count > 2:
        # if nmi not supplied
        if not powercor['nmi']:
            raise Exception("You have multiple NMIs in your portal. Please specify which one you want to use in .env using POWERCOR_NMI=")

        # find nmi on page
        try:
            nmi_found = driver.find_element_by_xpath("//input[@value='{}']/following::label".format(powercor['nmi']))
        except:
            raise Exception("POWERCOR_NMI of {} not found on page. Check you've entered it into .env correctly".format(powercor['nmi'])) from None

        # select nmi
        nmi_found.click()

    # click download data
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Download Data")]'))).click()

    logger("Logged in and clicked download data")

    # wait for meter data to load
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, "abc0")))

    logger("Meter data loaded")

    # wait for report type to be selectable
    WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//select/option[.='Detailed Report (CSV)']")))

    # select Detailed Report (CSV) - not using Select from selenium.webdriver.support.ui due to a js issue
    timeout = 0
    while timeout < 5:
        # get options
        options = driver.find_element_by_id('reportType').find_elements_by_tag_name('option')

        # if options loaded successfully
        if len(options) > 1:
            for option in options:
                if option.text == 'Detailed Report (CSV)':
                    option.click()
                    break

            # wait for button to be enabled
            if driver.find_element_by_xpath("//input[@value='Request Meter Data']").is_enabled():
                break

        # either options didn't load or button wasn't enabled, so sleep then try again
        driver.implicitly_wait(1)
        timeout+=1

    logger("Requesting file download using requests")

    today = datetime.now()

    # get form data
    # TODO: check what frmDate should be if less than 2 years of data
    form_data = {
        'j_id0:SiteTemplate:j_id158': 'j_id0:SiteTemplate:j_id158',
        'meter': 'Interval',
        'j_id0:SiteTemplate:j_id158:selMeterType': 'Interval',
        'j_id0:SiteTemplate:j_id158:selReportType': 'Detailed Report (CSV)',
        'j_id0:SiteTemplate:j_id158:selNMI': None,
        'j_id0:SiteTemplate:j_id158:frmDate': (today - relativedelta(years=2)).strftime("%d/%m/%Y"),
        'j_id0:SiteTemplate:j_id158:toDate': today.strftime("%d/%m/%Y"),
        'j_id0:SiteTemplate:j_id158:j_id235': 'Request Meter Data',
        'com.salesforce.visualforce.ViewState': None,
        'com.salesforce.visualforce.ViewStateVersion': None,
        'com.salesforce.visualforce.ViewStateMAC': None,
        'com.salesforce.visualforce.ViewStateCSRF': None
    }

    for key in form_data:
        # if a value is None, go and get it from the page
        if not form_data[key]:
            form_data[key] = driver.find_element_by_id(key).get_attribute("value")

    download_url = 'https://customermeterdata.portal.powercor.com.au/customermeterdata/CADRequestMeterData?selNMI={}'.format(form_data['j_id0:SiteTemplate:j_id158:selNMI'])

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "referrer": download_url,
    }

    with requests.session() as s:
        # get cookies from webdriver and set them in requests
        cookies = driver.get_cookies()
        for cookie in cookies:
            s.cookies.set(cookie['name'], cookie['value'])

        # download meter data
        response = s.post(
            download_url,
            data = form_data,
            headers = headers,
        )

        if response.ok:
            # get filename from content-disposition
            disposition = response.headers['content-disposition']
            filename = re.findall("filename=(.+)", disposition)[0]

            # save file
            with open(os.path.join(dir, filename), 'w', newline='') as file:
                file.write(response.text)

    logger("CSV should have been downloaded")