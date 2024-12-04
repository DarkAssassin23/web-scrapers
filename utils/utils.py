from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import csv, os
# Get the headers (specifically user agent) for the http get request
def getHeaders():
    return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0'}

# Exports the data dictionary to the specified
# csv file
def exportToCSV(dict, csvFileName):
    print("Generating \'"+csvFileName+"\'...")
    try:
        with open(csvFileName, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(dict.keys())
            writer.writerows(zip(*dict.values()))
    except:
        print("Error: unable to write to \'"+csvFileName+"\'. Make sure you have "+
            "permission to write to this file and it is not currently open and try again")

# Wait for page to load in the table, the table will be loaded 
# when the css_element tag passed in is visable
# we wait until we find that
def waitForPageToLoad(browser, css_element, retrys=0):
    if(retrys >= 10):
        print(f"Unable to find element on the page after {retrys} retrys. Exiting...")
        exit()
    try:
        delay = 1
        myElem = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_element)))
    except TimeoutException:
        waitForPageToLoad(browser, css_element, (retrys + 1))

# Checks to see if the provided file exists
def validFile(filename):
    if(not os.path.exists(filename)):
        print("Error: Could not find the file specified.")
        print("File \'"+filename+"\' does not exist")
        return False
    return True

# Save the links downloaded from a website to a file
def saveLinks(links, filename):
    try:
        with open(filename, "w") as f:
            for link in links:
                f.write(f'{link}\n')
    except:
        print(f"An error occurred writing to the file \'{filename}\'")

# Load the links downloaded from a website into a list
def loadLinks(filename):
    links = []
    if(not validFile(filename)):
        return links

    contents = []
    
    try:
        with open(filename, "r") as f:
            contents = f.readlines()
    except:
        print(f"An error occurred reading from the file \'{filename}\'")    

    for link in contents:
        links.append(link.strip())

    return links