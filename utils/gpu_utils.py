from requests import get
from bs4 import BeautifulSoup as bs

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utils.utils import *
from multiprocessing import Process, Queue
import os, time, random

numCPUs = os.cpu_count()
processes = []
baseURL = "https://www.videocardbenchmark.net/gpu.php?gpu="

# Extracts the name of the GPU from the website
def getGPUName(soup, gpuDict, verbose = False):
    name = soup.find('div', {"class":"desc-header"}).text.strip()
    if(verbose):
        print(name)
    gpuDict["Name"].append(name)

# Extracts the G3D and G2D scores for the GPU
def getGPUScores(soup, gpuDict):
    # Get G3D Mark Score
    data = soup.find("div", {"class":"right-desc"}).find_all("span")
    for item in data:
        if(item.text.isdigit()):
            gpuDict["G3D Mark Score"].append(item.text)
            break

    data = soup.find("div", {"class":"right-desc"}).text
    for item in data.strip().split("\n"):
        if(item.split(":")[0] == "Average G2D Mark"):
            gpuDict["G2D Mark Score"].append(item.split(":")[1].strip())
            return

# Check if the GPU class is embedded in the 'Other names' section
def checkGPUClass(data, gpuDict):
    for item in data:
        if(item.text.split(":")[0] == "Other names"):
            if("mobile" in item.text.split(":")[1].lower()):
                gpuDict["GPU Class"].append("Mobile")

# Fills in any blanks in data after the
# GPUs data has been gathered
def fillGaps(data, gpuDict):
    # Make sure all categories were filled out
    targetLen = len(gpuDict["Name"])
    if(len(gpuDict["GPU Class"]) < targetLen):
        checkGPUClass(data, gpuDict)

    for k,v in gpuDict.items():
        while(targetLen>len(v)):
            gpuDict[k].append("N/A")

# Extracts the details about the GPU from the website
# ex. Name, TDP, Core Clocks, Max Memory, Bus Interface, etc.
def getDetails(soup, gpuDict, verbose):
    getGPUName(soup, gpuDict, verbose)
    getGPUScores(soup, gpuDict)
    data = soup.find('div', {'class':'desc-body'}).find_all('p')
    for item in data:
        if(item.text.split(":")[0] == "Bus Interface"):
            gpuDict["Bus Interface"].append(item.text.split(":")[1].strip())
        elif(item.text.split(":")[0] == "Max Memory Size"):
            gpuDict["Max Memory (MB)"].append(item.text.split(":")[1].strip().split()[0])
        elif(item.text.split(":")[0] == "Core Clock(s)"):
            # Some GPUs have multiple clocks and this gets the last one
            speed = item.text.split(":")[1].strip().split()[0].split(",")[-1].split()[0]
            gpuDict["Core Clock(s) (MHz)"].append(speed)
        elif(item.text.split(":")[0] == "Memory Clock(s)"):
            # Some GPUs have multiple clocks and this gets the last one
            speed = item.text.split(":")[1].strip().split()[0].split(",")[-1].split()[0]
            # Some GPUs have Parentheses around the clock, so we'll remove it
            speed = speed.replace("(", "").replace(")","")
            gpuDict["Memory Clock(s) (MHz)"].append(speed)
        elif(item.text.split(":")[0] == "Videocard Category"):
            gpuDict["GPU Class"].append(item.text.split(":")[1].strip().split()[0])
        elif(item.text.split(":")[0] == "Videocard First Benchmarked"):
            gpuDict["First Tested"].append(item.text.split(":")[1].strip().split()[0])
        elif(item.text.split(":")[0] == "Max TDP"):
            gpuDict["TDP (W)"].append(item.text.split(":")[1].strip().split()[0])

    fillGaps(data, gpuDict)

# Adds a ranking based on G3D Mark Score and
# G2D Mark Score
def rankGPUs(gpuDict):
    g3dScores = []
    g2dScores = []
    for x in range(len(gpuDict["Name"])):
        if(not (gpuDict["G3D Mark Score"][x] == "N/A")):
            g3dScores.append(int(gpuDict["G3D Mark Score"][x]))
        else:
            g3dScores.append(0)
        if(not (gpuDict["G2D Mark Score"][x] == "N/A")):
            g2dScores.append(int(gpuDict["G2D Mark Score"][x]))
        else:
            g2dScores.append(0)

    g3dScores.sort(reverse=True)
    g2dScores.sort(reverse=True)

    gpuDict["G3D Mark Rank"] = [None] * len(gpuDict["Name"])
    gpuDict["G2D Mark Rank"] = [None] * len(gpuDict["Name"])
    
    for x in range(len(gpuDict["Name"])):
        if(gpuDict["G3D Mark Score"][x] == "N/A"):
            gpuDict["G3D Mark Rank"][x] = "N/A";
        else:
            gpuDict["G3D Mark Rank"][x] = g3dScores.index(int(gpuDict["G3D Mark Score"][x]))+1
        if(gpuDict["G2D Mark Score"][x] == "N/A"):
            gpuDict["G2D Mark Rank"][x] = "N/A"
        else:
            gpuDict["G2D Mark Rank"][x] = g2dScores.index(int(gpuDict["G2D Mark Score"][x]))+1

# Using the selenium webdriver, it opens a firefox session
# finds the selector to show all GPUs then pulls all their URLS
# and returns the result
def getAllGPULinks(verbose=False):
    try:
        if(verbose):
            print("Navigating to videocardbenchmark.net")
        options = Options()
        options.add_argument('-headless')
        browser = webdriver.Firefox(options=options)
        browser.get('https://www.videocardbenchmark.net/GPU_mega_page.html')
        select_field = browser.find_element(By.TAG_NAME, 'select')
        select_field.send_keys("All")
    except:
        print("Error: Unable to load page. Ensure all Firefox processes are stopped and try again")
        browser.quit()
        exit()

    waitForPageToLoad(browser, 'td[class=" details-control"]')

    html = browser.page_source
    browser.quit()

    if(verbose):
        print("Pulling HTML...")
    soup = bs(html, "html.parser")
    link_tags = soup.find('table', {'class': 'dataTable-blue'}).find_all('a', href=True)
    links = []
    if(verbose):
        print("Extracting links")

    # Note: If you don't want to pull all ~2500 GPUs, you can manually
    # specify the range.
    # Ex. `for link in link_tags[1700:2000]:` 
    # This will limit to total number of links to 300 between items
    # 1700 and 2000 in the list
    for link in link_tags:
        link = link['href']
        link = link[link.find("=")+1:]
        links.append(f"{baseURL}{link}")

    return links

# Function to get the results for the list of cpu's provided
def gatherResults(gpus, queue, verbose=False):
    gpuDict = {
    "Name":[],
    "GPU Class":[],
    "First Tested":[],
    "G3D Mark Score":[],
    "G2D Mark Score":[],
    "Max Memory (MB)":[],
    "Core Clock(s) (MHz)":[],
    "Memory Clock(s) (MHz)":[],
    "TDP (W)":[],
    "Bus Interface":[]
    }

    for gpu in gpus:
        currentGPU = gpu
        try:
            headers = getHeaders()
            result = get(gpu, headers=headers)
            soup = bs(result.content, "html.parser")
            getDetails(soup, gpuDict, verbose)
        except KeyboardInterrupt:
            exit()
        except:
            print("\nAn error occurred gathering GPU data on the following GPU \'"+currentGPU+"\'.")

    queue.put(gpuDict)
    return gpuDict
    
# Evenly splits the number of cpu's to get by
# the desired number of processes to run, up to
# the maximum number the computer has, to get the
# data in parallel to speed up the process
def multiProcess(gpus, processesToRun, verbose=False):
    gpuDict = {
    "Name":[],
    "GPU Class":[],
    "First Tested":[],
    "G3D Mark Score":[],
    "G2D Mark Score":[],
    "Max Memory (MB)":[],
    "Core Clock(s) (MHz)":[],
    "Memory Clock(s) (MHz)":[],
    "TDP (W)":[],
    "Bus Interface":[]
    }
    
    if(processesToRun > numCPUs):
        processesToRun = numCPUs
    if(processesToRun > len(gpus)):
        processesToRun = len(gpus)
        
    queue = Queue(processesToRun)
    numCPUsPerProcess = len(gpus) // processesToRun
    extra = len(gpus) % processesToRun
    start = 0
   
    for x in range(processesToRun):
        gpusToGet = []
        end = start+numCPUsPerProcess
        if(extra>0):
            end += 1
            extra -= 1
          
        gpusToGet = gpus[start:end]
        start = end
        
        p = Process(target=gatherResults, args=(gpusToGet, queue, verbose))
        processes.append(p)
        p.start()
    
    while(not queue.full()):
        pass
        
    for x in range(processesToRun):
        d = queue.get()
        for k,v in d.items():
            for x in v:
                gpuDict[k].append(x)

    return gpuDict