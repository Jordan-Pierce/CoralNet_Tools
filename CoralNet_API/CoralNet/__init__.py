import os
import io
import sys
import time
import tqdm
import glob
import json
import requests
import datetime
from tqdm import tqdm

import argparse
from gooey import Gooey, GooeyParser

import re
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

import concurrent
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC


# -------------------------------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------------------------------

# Constant for the CoralNet url
CORALNET_URL = "https://coralnet.ucsd.edu"

# CoralNet Source page, lists all sources
CORALNET_SOURCE_URL = CORALNET_URL + "/source/about/"

# CoralNet Labelset page, lists all labelsets
CORALNET_LABELSET_URL = CORALNET_URL + "/label/list/"

# URL of the login page
LOGIN_URL = "https://coralnet.ucsd.edu/accounts/login/"

# Image Formats
IMG_FORMATS = ["jpg", "jpeg", "png", "tif", "tiff", "bmp"]

# CoralNet functional groups
FUNC_GROUPS_LIST = [
    "Other Invertebrates",
    "Hard coral",
    "Soft Substrate",
    "Hard Substrate",
    "Other",
    "Algae",
    "Seagrass"]

# Mapping from group to ID
FUNC_GROUPS_DICT = {
    "Other Invertebrates": "14",
    "Hard coral": "10",
    "Soft Substrate": "15",
    "Hard Substrate": "16",
    "Other": "18",
    "Algae": "19",
    "Seagrass": "20"}


# -------------------------------------------------------------------------------------------------
# Functions to authenticate with CoralNet
# -------------------------------------------------------------------------------------------------


def authenticate(username, password):
    """
    Authenticate with CoralNet; used to make sure user has the correct credentials.
    """

    print("\n###############################################")
    print("Authentication")
    print("###############################################\n")
    print(f"NOTE: Authenticating user {username}")

    # Send a GET request to the login page to retrieve the login form
    response = requests.get(LOGIN_URL)

    # Pass along the cookies
    cookies = response.cookies

    # Parse the HTML of the response using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the CSRF token from the HTML of the login page
    csrf_token = soup.find("input", attrs={"name": "csrfmiddlewaretoken"})

    # Create a dictionary with the login form fields and their values
    # (replace "username" and "password" with your actual username and
    # password)
    data = {
        "username": username,
        "password": password,
        "csrfmiddlewaretoken": csrf_token["value"],
    }

    # Include the "Referer" header in the request
    headers = {
        "Referer": LOGIN_URL,
    }

    # Use requests.Session to create a session that will maintain your login
    # state
    with requests.Session() as session:

        # Use session.post() to submit the login form, including the
        # "Referer" header
        response = session.post(LOGIN_URL,
                                data=data,
                                headers=headers,
                                cookies=cookies)

        if "credentials you entered did not match" in response.text:
            raise Exception(f"ERROR: Authentication unsuccessful for '{username}'\n "
                            f"Please check that your usename and password are correct")
        else:
            print(f"NOTE: Authentication successful for {username}")


def check_for_browsers(headless):
    """
    Check if Chrome, Firefox, and Edge browsers are installed.
    """

    print("\n###############################################")
    print("Browser")
    print("###############################################\n")

    options = Options()

    if headless:
        # Add headless argument
        options.add_argument('headless')
        # Needed to avoid timeouts when running in headless mode
        options.add_experimental_option('extensionLoadTimeout', 3600000)

    # heck for Chrome, Firefox, and Edge browsers
    try:
        exe_path = ChromeDriverManager().install()
        browser = webdriver.Chrome(executable_path=exe_path, options=options)
        print("NOTE: Using Google Chrome")
        return browser

    except Exception as e:
        print("WARNING: Google Chrome could not be used")

    print("ERROR: No browsers are installed. Exiting")
    sys.exit(1)


def login(driver):
    """
    Log in to CoralNet using Selenium.
    """

    print("\n###############################################")
    print("Login")
    print("###############################################\n")

    # Create a variable for success
    success = False

    # Navigate to the page to login
    driver.get(CORALNET_URL + "/accounts/login/")

    # Find the username button
    path = "id_username"
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, path)))

    # Find the password button
    path = "id_password"
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, path)))

    # Find the login button
    path = "//input[@type='submit'][@value='Sign in']"
    login_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, path)))

    # Enter the username and password
    username_input.send_keys(driver.capabilities['credentials']['username'])
    password_input.send_keys(driver.capabilities['credentials']['password'])

    # Click the login button
    time.sleep(3)
    login_button.click()

    # Confirm login was successful; after 60 seconds, throw an error.
    try:
        path = "//a[@href='/accounts/logout/']/span[text()='Sign out']"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, path)))

        # Login was successful
        success = True

        print(f"NOTE: Successfully logged in for {driver.capabilities['credentials']['username']}")

    except Exception as e:
        raise ValueError(f"ERROR: Could not login with "
                         f"{driver.capabilities['credentials']['username']}\n{e}")

    return driver, success


def check_permissions(driver):
    """
    Check if the user has permission to access the page.
    """

    try:
        # First check that this is existing source the user has access to
        path = "content-container"
        status = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, path)))

        # Check the status
        if not status.text:
            raise Exception(f"ERROR: Unable to access page information")

    except Exception as e:
        print(f"ERROR: {e} Exiting.")
        sys.exit(1)

    return driver, status


def get_token(username, password):
    """
    Retrieves a CoralNet authentication token for API requests.
    """
    # Requirements for authentication
    CORALNET_AUTH = CORALNET_URL + "/api/token_auth/"
    HEADERS = {"Content-type": "application/vnd.api+json"}
    PAYLOAD = {"username": username, "password": password}

    # Response from CoralNet when provided credentials
    response = requests.post(CORALNET_AUTH,
                             data=json.dumps(PAYLOAD),
                             headers=HEADERS)

    if response.ok:

        print("NOTE: API token retrieved successfully")

        # Get the coralnet token returned to the user
        CORALNET_TOKEN = json.loads(response.content.decode())['token']

        # Update the header to contain the user's coralnet token
        HEADERS = {"Authorization": f"Token {CORALNET_TOKEN}",
                   "Content-type": "application/vnd.api+json"}

    else:
        raise ValueError(f"ERROR: Could not retrieve API token\n{response.content}")

    return CORALNET_TOKEN, HEADERS