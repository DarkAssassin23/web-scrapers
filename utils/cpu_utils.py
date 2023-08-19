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
import os, time

numCPUs = os.cpu_count()
processes = []
baseURL = "https://www.cpubenchmark.net/cpu.php?cpu="

# Extracts the name of the CPU from the website
def getCPUName(soup, cpuDict, verbose = False):
    name = soup.find('div', {"class":"desc-header"}).text.strip()
    if(verbose):
        print(name)
    cpuDict["Name"].append(name)
    if("[Dual CPU]" in name):
        return 2
    elif("[Quad CPU]" in name):
        return 4
    else:
        return 1

# Extracts the single thread rating of the CPU from the website
def getSingleThreadedScore(soup, cpuDict):
    data = soup.find("div", {"class":"right-desc"}).text
    for item in data.strip().split("\n"):
        if(item.split(":")[0] == "Single Thread Rating"):
            cpuDict[item.split(":")[0]].append(item.split(":")[1].strip())
            return
    cpuDict["Single Thread Rating"].append("N/A")

# Extracts the class of the CPU from the website
# ex. Laptop, Desktop, Server
def getChipType(soup, cpuDict):
    data = soup.find("div", {"class" : "left-desc-cpu"}).text
    for item in data.strip().split("\n"):
        if(item.split(":")[0] == "Class" and item.split(":")[1].strip() != ""):
            cpuDict["CPU Class"].append(item.split(":")[1].strip())
            return
    cpuDict["CPU Class"].append("N/A")

# Extracts the type of socket the CPU is made for from the website
def getSocketType(soup, cpuDict):
    data = soup.find("div", {"class" : "left-desc-cpu"}).text
    for item in data.strip().split("\n"):
        if(item.split(":")[0] == "Socket" and item.split(":")[1].strip() != ""):
            cpuDict["Socket"].append(item.split(":")[1].strip())
            return
    cpuDict["Socket"].append("N/A")

# Extracts the quarter and year the CPU was released from the website
def getTimeOfRelease(soup, cpuDict):
    data = soup.find_all('p', {'class' : 'alt'})
    for item in data:
        if("CPU First Seen on Charts:" in item.text):
            cpuDict["Launched"].append(item.text.split(":")[1].strip())
            return
    cpuDict["Launched"].append("N/A")

# Extracts the Overall Score of the CPU from the website
def getOverallScore(soup, cpuDict):
    data = soup.find("div", {"class":"right-desc"}).find_all("span")
    for item in data:
        if(item.text.isdigit()):
            cpuDict["Overall Score"].append(item.text)
            return

# Extracts the Typical TDP usage of the CPU
def getTDP(data, numPhysicalCPUs):
    for item in data:
        if("Typical TDP" in item.text):
            # Some CPUs have decimals in their wattages  
            tdp = int(round(float(item.text.split(":")[1].strip().split(" ")[0]))) * numPhysicalCPUs
            # Some CPUs have a negative tdp some how?
            # Ex. Intel Core2 Duo E8335 @ 2.66GHz (as of Aug. 8, 2023)
            if(tdp < 0):
                tdp = "N/A"
            return f"{tdp}"
    return "N/A"

# Extracts the number of CPU cores and threads
def getCoresAndThreads(data, numPhysicalCPUs, cpuDict):
    threadsPresent = ("Threads" in data.text)
    if(data.text.split(":")[0] == "Cores"):
        coresAndThreads = data.text.replace(":", "").split(" ")
        # Cores
        cpuDict[coresAndThreads[0]].append(int(coresAndThreads[1]) * numPhysicalCPUs)
        # Threads
        if(threadsPresent):
            cpuDict[coresAndThreads[2]].append(int(coresAndThreads[3]) * numPhysicalCPUs)
        else:
            cpuDict["Threads"].append(int(coresAndThreads[1]) * numPhysicalCPUs)
    else:
        coresAndThreads = data.text.split(":")[1].split(",")
        cores = coresAndThreads[0].strip().split(" ")
        threads = coresAndThreads[1].strip().split(" ")

        cpuDict[cores[1]].append(int(cores[0]) * numPhysicalCPUs)
        cpuDict[threads[1]].append(int(threads[0]) * numPhysicalCPUs)

# Extracts the CPU base clockspeed and turbo speed
def getClockspeedAndTurbo(data, cpuDict):
    component = data.text.split(":")[0]
    if(component == "Clockspeed" or component == "Turbo Speed"):
        speed = data.text.split(":")[1].strip().split()[0]
        # Some clockspeeds are in MHz rather than GHz, so well fix that
        if("," in speed):
            speed = float(speed.replace(".","").replace(",","."))
            speed = round(speed, 1) 
        cpuDict[f'{component} (GHz)'].append(str(speed))
    else:
        pivot = data.text.find("Threads")
        pivot += data.text[pivot:].find(",") + 1
        base = data.text[pivot:].split(",")[0].strip()
        turbo = data.text[pivot:].split(",")[1].strip()

        baseComponents = base.split(" ")
        turboComponents = turbo.split(" ")

        # Some clockspeeds are in MHz rather than GHz, so well fix that
        baseSpeed = baseComponents[0]
        turboSpeed = turboComponents[0]

        if("," in baseSpeed):
            baseSpeed = float(baseSpeed.replace(".","").replace(",","."))
            baseSpeed = round(baseSpeed, 1)

        if("," in turboSpeed):
            turboSpeed = float(turboComponents[0].replace(".","").replace(",","."))
            turboSpeed = round(turboSpeed, 1)

        if(baseSpeed == 'NA'):
            cpuDict["Clockspeed (GHz)"].append("N/A")
        else:
            cpuDict["Clockspeed (GHz)"].append(f"{baseSpeed}")

        if(turboSpeed == 'NA'):
            cpuDict["Turbo Speed (GHz)"].append("N/A")
        else:
            cpuDict["Turbo Speed (GHz)"].append(f"{turboSpeed}")


# Extracts the additional details about the CPU from the website
# ex. TDP, Number of Cores, Number of Threads, Clockspeeds, etc.
def getDetails(soup, numPhysicalCPUs, cpuDict):
    data = soup.find('div', {'class':'desc-body'}).find_all('p')
    cpuDict["TDP (W)"].append(getTDP(data, numPhysicalCPUs))
    for item in data: 
        if(item.text != ""):
            component = item.text.split(":")[0]
            componentData = item.text.split(":")[1]
            if(component == "Cores" or component == "Total Cores"):
                getCoresAndThreads(item, numPhysicalCPUs, cpuDict)
            
            if(component == "Performance Cores" or component == "Primary Cores" 
                or component == "Clockspeed" or component == "Turbo Speed"):
                getClockspeedAndTurbo(item, cpuDict)
    if(len(cpuDict["Name"]) > len(cpuDict["Turbo Speed (GHz)"])):
        cpuDict["Turbo Speed (GHz)"].append("N/A")
    if(len(cpuDict["Name"]) > len(cpuDict["Clockspeed (GHz)"])):
        cpuDict["Clockspeed (GHz)"].append("N/A")

# Adds a ranking based on overall score and
# single threaded score
def rankCPUs(cpuDict):
    overallScores = []
    singleThreadScores = []
    for x in range(len(cpuDict["Name"])):
        if(not (cpuDict["Overall Score"][x] == "N/A")):
            overallScores.append(int(cpuDict["Overall Score"][x]))
        else:
            overallScores.append(0)
        if(not (cpuDict["Single Thread Rating"][x] == "N/A")):
            singleThreadScores.append(int(cpuDict["Single Thread Rating"][x]))
        else:
            singleThreadScores.append(0)

    overallScores.sort(reverse=True)
    singleThreadScores.sort(reverse=True)

    cpuDict["Overall Rank"] = [None] * len(cpuDict["Name"])
    cpuDict["Single Threaded Rank"] = [None] * len(cpuDict["Name"])
    
    for x in range(len(cpuDict["Name"])):
        if(cpuDict["Overall Score"][x] == "N/A"):
            cpuDict["Overall Rank"][x] = "N/A";
        else:
            cpuDict["Overall Rank"][x] = overallScores.index(int(cpuDict["Overall Score"][x]))+1
        if(cpuDict["Single Thread Rating"][x] == "N/A"):
            cpuDict["Single Threaded Rank"][x] = "N/A"
        else:
            cpuDict["Single Threaded Rank"][x] = singleThreadScores.index(int(cpuDict["Single Thread Rating"][x]))+1

# Using the selenium webdriver, it opens a firefox session
# finds the selector to show all CPUs then pulls all their URLS
# and returns the result
def getAllCPULinks(verbose=False):
    try:
        if(verbose):
            print("Navigating to cpubenchmark.net")
        options = Options()
        options.add_argument('-headless')
        browser = webdriver.Firefox(options=options)
        browser.get('https://www.cpubenchmark.net/CPU_mega_page.html')
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

    # Note: If you don't want to pull all ~5000 CPUs, you can manually
    # specify the range.
    # Ex. `for link in link_tags[2700:3000]:` 
    # This will limit to total number of links to 300 between items
    # 2700 and 3000 in the list
    for link in link_tags:
        link = link['href']
        link = link[link.find("=")+1:]
        links.append(f"{baseURL}{link}")

    return links

# Function to get the results for the list of cpu's provided
def gatherResults(cpus, queue, verbose=False):
    cpuDict = {
    "Name":[],
    "CPU Class":[],
    "Socket":[],
    "Launched":[],
    "Overall Score":[],
    "Single Thread Rating":[],
    "Clockspeed (GHz)":[],
    "Turbo Speed (GHz)":[],
    "TDP (W)":[],
    "Cores":[],
    "Threads":[]
    }
    for cpu in cpus:
        currentCPU = cpu
        try:
            result = get(cpu)
            soup = bs(result.content, "html.parser")

            sup = soup.find_all('sup')
            for x in sup:
                x.replaceWith('')

            numPhysicalCPUs = getCPUName(soup, cpuDict, verbose)
            getChipType(soup, cpuDict)
            getSocketType(soup, cpuDict)
            getTimeOfRelease(soup, cpuDict)
            getOverallScore(soup, cpuDict)
            getSingleThreadedScore(soup, cpuDict)
            getDetails(soup, numPhysicalCPUs, cpuDict)
        except KeyboardInterrupt:
            exit()
        except:
            print("\nAn error occurred gathering CPU data on the following CPU \'"+currentCPU+"\'.")

    queue.put(cpuDict)
    return cpuDict

    
# Evenly splits the number of cpu's to get by
# the desired number of processes to run, up to
# the maximum number the computer has, to get the
# data in parallel to speed up the process
def multiProcess(cpus, processesToRun, verbose=False):
    cpuDict = {
    "Name":[],
    "CPU Class":[],
    "Socket":[],
    "Launched":[],
    "Overall Score":[],
    "Single Thread Rating":[],
    "Clockspeed (GHz)":[],
    "Turbo Speed (GHz)":[],
    "TDP (W)":[],
    "Cores":[],
    "Threads":[]
    }
    
    if(processesToRun > numCPUs):
        processesToRun = numCPUs
    if(processesToRun > len(cpus)):
        processesToRun = len(cpus)
        
    queue = Queue(processesToRun)
    numCPUsPerProcess = len(cpus) // processesToRun
    extra = len(cpus) % processesToRun
    start = 0
   
    for x in range(processesToRun):
        cpusToGet = []
        end = start+numCPUsPerProcess
        if(extra>0):
            end += 1
            extra -= 1
          
        cpusToGet = cpus[start:end]
        start = end
        
        p = Process(target=gatherResults, args=(cpusToGet, queue, verbose))
        processes.append(p)
        p.start()
    
    while(not queue.full()):
        pass
        
    for x in range(processesToRun):
        d = queue.get()
        for k,v in d.items():
            for x in v:
                cpuDict[k].append(x)

    return cpuDict