import requests
import os
import json
from dotenv import load_dotenv

urls = {
    'auth': 'https://api-bff.amberelectric.com.au/api/v1.0/Authentication/SignIn',
    'usage': 'https://api-bff.amberelectric.com.au/api/v1.0/UsageHub/GetUsageForHub'
}

# these will be loaded in from .env
username = None
password = None
tokens = {}

def main():
    loadDotEnv()

    authenticate()

    getUsage()

def loadDotEnv():
    global username
    global password
    
    load_dotenv()

    username = os.getenv("AMBER_USERNAME")
    password = os.getenv("AMBER_PASSWORD")

    if not username:
        raise ValueError("Specify AMBER_USERNAME in .env file")
    if not password:
        raise ValueError("Specify PASSWORD in .env file")

def authenticate():
    global username
    global password
    global tokens

    data = {
        'username': username,
        'password': password
    }

    headers = {
        'content-type': 'application/json'
    }

    response = requests.post(urls['auth'], headers=headers, data=json.dumps(data))
    responseData = response.json()

    if not responseData.get('data'):
        raise Exception(f"We didn't get data back: {json.dumps(responseData,indent=2)}")

    # store in redis?
    tokens = {
        'refreshtoken': responseData['data']['refreshToken'],
        'authorization': responseData['data']['idToken']
    }

def getUsage():
    global tokens

    headers = tokens

    response = requests.post(urls['usage'], headers=headers)
    responseData = response.json()

    if not responseData.get('data'):
        raise Exception(f"We didn't get data back: {json.dumps(responseData,indent=2)}")

    # sort the response in case it doesn't arrive sorted
    responseData['data']['thisWeekDailyUsage'].sort(key=lambda item:item['date'], reverse=True)

    # get first day
    print(f"Yesterday you used: {responseData['data']['thisWeekDailyUsage'][0]['usageKWH']}KWH")

if __name__ == "__main__":
    main()