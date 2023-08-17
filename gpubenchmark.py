#!/usr/bin/env python3
import csv, os, argparse, time, random

from utils.gpu_utils import *
from utils.utils import *

# Default csv file
csvFileName = "gpuData.csv"
numPhysicalCPUs = 1
gpuDataDict = {
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Web scraper to pull GPU data from videocardbenchmark.net')
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

    # try:
    start = time.time()

    # gpuLinks = getAllGPULinks(verbose)
    # saveLinks(gpuLinks, "gpu_links.txt")
    gpuLinks = loadLinks("gpu_links.txt")

    # For random testing
    # start = random.randint(0, (len(gpuLinks)-30))
    # gpuLinks = gpuLinks[start:(start+25)]
    tmp = []
    for _ in range(0,20):
        gpu = random.randint(0, (len(gpuLinks)))
        tmp.append(gpuLinks[gpu])
    gpuLinks = tmp

    if(verbose):
        print("Gathering GPU Data")
    if(singleThreaded):
        gpuDataDict = gatherResults(gpuLinks, Queue(1), verbose)
    else:
        gpuDataDict = multiProcess(gpuLinks, cpusToUse, verbose)

    print(gpuDataDict)
    if(verbose):
        print("Ranking GPUs")
    rankGPUs(gpuDataDict)
    exportToCSV(gpuDataDict, csvFileName)
    finalTime = time.time() - start

    print("done.")
    print(f"Finished in: {finalTime} seconds")
        
    # except:
    #     print("\nAn error occurred during processing")
