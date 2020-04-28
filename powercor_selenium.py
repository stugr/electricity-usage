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
chromedriver = os.path.join(dir, "chromedriver.exe")

# debug logger
def logger():
    global log_count
    global driver
    global dir
    global debug

    if debug:
        print(log_count)
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
options.add_argument(headless)
options.add_argument("log-level=3")
options.add_experimental_option("prefs", {
  "download.default_directory": dir,
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})

driver = webdriver.Chrome(executable_path=chromedriver, options=options)

# load login page 
driver.get('https://customermeterdata.portal.powercor.com.au/customermeterdata/CADAccountPage?startURL=%2Fcustomermeterdata%2FCADAccountPage')

logger()

# fill in username/password and click login
driver.find_element_by_id('j_id0:SiteTemplate:j_id297:loginComponent:loginForm:username').send_keys(powercor['username'])
driver.find_element_by_id('j_id0:SiteTemplate:j_id297:loginComponent:loginForm:password').send_keys(powercor['password'])
driver.find_element_by_id('j_id0:SiteTemplate:j_id297:loginComponent:loginForm:loginButtonAccountPage').click()

logger()

# click download data
WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Download Data")]'))).click()

logger()

# wait for meter data to load
WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, "abc0")))

logger()

# wait for report type to be selectable, then select detailed report (csv)
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "reportType")))
Select(driver.find_element_by_id('reportType')).select_by_visible_text('Detailed Report (CSV)')

# wait then click request meter data
time.sleep(1)
driver.find_element_by_xpath("//input[@value='Request Meter Data']").click()

logger()

# sleep until csv exists (should add a timeout)
while not glob.glob('*CITIPOWER_DETAILED.csv'):
    time.sleep(1)

logger()

driver.quit()