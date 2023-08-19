#!/usr/bin/env python3
import csv, os, argparse, time, sys

sys.path.append('../')

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
    except KeyboardInterrupt:
        print("\nExiting...")
    except:
        print("\nAn error occurred during processing")
