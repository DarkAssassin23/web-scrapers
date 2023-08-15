#!/usr/bin/env python3
import csv, os, argparse, time

from utils.cpu_utils import *
from utils.utils import *

# Default csv file
csvFileName = "cpuData.csv"
numPhysicalCPUs = 1
cpuDataDict = {
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

# Checks to see if the CPU list file exists
def validInputFile():
    if(not os.path.exists(cpuListFileName)):
        print("Error: Could not find the file specified.")
        print("File \'"+cpuListFileName+"\' does not exist")
        return False
    return True

# Gets a list of all the CPUs from the
# list of CPUs file
def getCPUs():
    lines = ""
    cpus = []
    with open(cpuListFileName, 'r') as f:
        lines = f.readlines()
    for line in lines:
        # Find where comments start and ignore everything
        # after the start of the comment
        if(line.find("#") != -1 or line.find("//") != -1):
            if(min(line.find("#"), line.find("//")) != -1):
                line = line[:min(line.find("#"), line.find("//"))]
            else:
                line = line[:max(line.find("#"), line.find("//"))]
        if(not line.strip() == ''):
            cpus.append(line.strip())
    return cpus

# Adds any auxiliary data to the respective cpu
def addAuxData(currentData, cpuDict):
    for k,v in currentData.items():
        # If k is not in cpuDict it is auxiliary
        if not k in cpuDict:
            count = 0
            cpuDict[k] = [None] * len(cpuDict["Name"])
            for curName in cpuDict["Name"]:
                if(curName in currentData["Name"]):
                    cpuDict[k][count] = currentData[k][currentData["Name"].index(curName)]
                else:
                    cpuDict[k][count] = "N/A"

                count += 1

# If the output CSV file exists, it gets read in
# so if you added additional info to the csv
# that info will be transfered, if the cpu exists
def readCSV():
    d={}
    if(os.path.exists(csvFileName)):
        with open(csvFileName, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for k, v in row.items():
                    if not k in d:
                        d[k] = []
                    d[k].append(v)
    return d


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Web scraper to pull CPU data from cpubenchmark.net')
    parser.add_argument('-o', nargs=1, metavar="file", help="output file to save data to")
    parser.add_argument('-p', nargs='?', type=int, const=numCPUs, metavar="processes",
        help="the number of processes you would like to run. If left blank, it will run with the maximum number of available CPUs")
    parser.add_argument('-v', action="store_true", help="Turn on verbose mode")

    singleThreaded = True
    cpusToUse = 0

    args = parser.parse_args()

    if(args.o is not None):
        csvFileName = str(args.o[0])
    if(args.p is not None):
        cpusToUse = args.p
        singleThreaded = False
    verbose = args.v

    try:
        start = time.time()

        cpuLinks = getAllCPULinks(verbose)

        if(verbose):
            print("Gathering CPU Data")
        if(singleThreaded):
            cpuDataDict = gatherResults(cpuLinks, Queue(1), verbose)
        else:
            cpuDataDict = multiProcess(cpuLinks, cpusToUse, verbose)
        
        if(verbose):
            print("Ranking CPUs")
        rankCPUs(cpuDataDict)
        exportToCSV(cpuDataDict, csvFileName)
        finalTime = time.time() - start

        print("done.")
        print("Finished in: "+str(finalTime)+" seconds")
        
    except:
        print("\nAn error occurred during processing")
